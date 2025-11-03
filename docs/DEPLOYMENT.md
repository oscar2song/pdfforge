# 🚀 PDFForge Deployment Guide

Complete guide for deploying PDFForge to production environments.

## 📋 Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Local Production Setup](#local-production-setup)
- [Docker Deployment](#docker-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Environment Configuration](#environment-configuration)
- [Security Best Practices](#security-best-practices)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests pass (`pytest`)
- [ ] Security review completed
- [ ] Environment variables configured
- [ ] Secret keys generated
- [ ] SSL/TLS certificates obtained
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Error tracking setup
- [ ] Load testing completed
- [ ] Documentation updated

## 🏠 Local Production Setup

### Prerequisites

- Python 3.11+
- Virtual environment
- Production-grade WSGI server (Gunicorn)
- Reverse proxy (Nginx)
- Process manager (systemd or supervisord)

### Step 1: Prepare Application

```bash
# Clone repository
git clone https://github.com/oscar2song/pdfforge.git
cd pdfforge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Set up directories
mkdir -p uploads downloads temp logs
chmod 755 uploads downloads temp logs
```

### Step 2: Configure Environment

Create `.env` file:

```bash
# Application
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this
MAX_CONTENT_LENGTH=524288000

# Paths
UPLOAD_FOLDER=/var/www/pdfforge/uploads
DOWNLOAD_FOLDER=/var/www/pdfforge/downloads
TEMP_FOLDER=/var/www/pdfforge/temp
LOG_FOLDER=/var/www/pdfforge/logs

# Tesseract (if using OCR)
TESSERACT_CMD=/usr/bin/tesseract

# Database (if applicable)
DATABASE_URL=postgresql://user:password@localhost/pdfforge

# Redis (for caching/queues)
REDIS_URL=redis://localhost:6379/0
```

Generate secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Set Up Gunicorn

Create `gunicorn_config.py`:

```python
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2

# Logging
accesslog = "/var/www/pdfforge/logs/gunicorn_access.log"
errorlog = "/var/www/pdfforge/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "pdfforge"

# Server mechanics
daemon = False
pidfile = "/var/www/pdfforge/gunicorn.pid"
umask = 0
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if not using reverse proxy)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

### Step 4: Configure Nginx

Create `/etc/nginx/sites-available/pdfforge`:

```nginx
upstream pdfforge {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name pdfforge.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name pdfforge.example.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/pdfforge.crt;
    ssl_certificate_key /etc/ssl/private/pdfforge.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Logging
    access_log /var/log/nginx/pdfforge_access.log;
    error_log /var/log/nginx/pdfforge_error.log;
    
    # Max upload size
    client_max_body_size 500M;
    client_body_timeout 300s;
    
    # Proxy settings
    location / {
        proxy_pass http://pdfforge;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Static files
    location /static {
        alias /var/www/pdfforge/pdfforge/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/pdfforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Create Systemd Service

Create `/etc/systemd/system/pdfforge.service`:

```ini
[Unit]
Description=PDFForge Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/pdfforge
Environment="PATH=/var/www/pdfforge/.venv/bin"
ExecStart=/var/www/pdfforge/.venv/bin/gunicorn -c gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pdfforge
sudo systemctl start pdfforge
sudo systemctl status pdfforge
```

## 🐳 Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application
COPY .. .

# Create directories
RUN mkdir -p uploads downloads temp logs

# Non-root user
RUN useradd -m -u 1000 pdfforge && \
    chown -R pdfforge:pdfforge /app
USER pdfforge

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  pdfforge:
    build: .
    container_name: pdfforge
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./downloads:/app/downloads
      - ./temp:/app/temp
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - MAX_CONTENT_LENGTH=524288000
    env_file:
      - .env
    networks:
      - pdfforge_network
    
  nginx:
    image: nginx:alpine
    container_name: pdfforge_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./pdfforge/static:/usr/share/nginx/html/static:ro
    depends_on:
      - pdfforge
    networks:
      - pdfforge_network

networks:
  pdfforge_network:
    driver: bridge
```

### Deploy with Docker

```bash
# Build image
docker build -t pdfforge:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ☁️ Cloud Platforms

### AWS Elastic Beanstalk

1. **Install EB CLI**
```bash
pip install awsebcli
```

2. **Initialize EB**
```bash
eb init -p python-3.12 pdfforge
```

3. **Create environment**
```bash
eb create pdfforge-prod
```

4. **Deploy**
```bash
eb deploy
```

5. **Configuration files**

Create `.ebextensions/01_packages.config`:
```yaml
packages:
  yum:
    tesseract: []
```

Create `.ebextensions/02_python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
```

### Google Cloud Platform (GCP)

1. **Create app.yaml**
```yaml
runtime: python312
entrypoint: gunicorn -b :$PORT app:app

instance_class: F2

automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 10

env_variables:
  FLASK_ENV: "production"
  SECRET_KEY: "your-secret-key"
```

2. **Deploy**
```bash
gcloud app deploy
```

### Microsoft Azure

1. **Create requirements.txt with Gunicorn**
```txt
Flask==3.1.2
PyMuPDF==1.26.5
gunicorn==21.2.0
# ... other dependencies
```

2. **Deploy to Azure App Service**
```bash
az webapp up --name pdfforge --resource-group myResourceGroup --runtime "PYTHON:3.12"
```

### Heroku

1. **Create Procfile**
```
web: gunicorn app:app
```

2. **Deploy**
```bash
heroku create pdfforge
git push heroku main
```

3. **Configure**
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key
```

### DigitalOcean App Platform

1. **Create .do/app.yaml**
```yaml
name: pdfforge
services:
- name: web
  github:
    repo: oscar2song/pdfforge
    branch: main
  run_command: gunicorn -w 4 app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: FLASK_ENV
    value: production
```

2. **Deploy via dashboard or CLI**
```bash
doctl apps create --spec .do/app.yaml
```

## 🔧 Environment Configuration

### Production Settings

Create `config.py` for production:

```python
import os

class ProductionConfig:
    """Production configuration."""
    
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600
    
    # Upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 524288000))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER', 'downloads')
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', 'temp')
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/pdfforge.log')
    
    # Performance
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
```

### Environment Variables

Required:
- `SECRET_KEY` - Flask secret key
- `FLASK_ENV` - Set to "production"

Optional:
- `MAX_CONTENT_LENGTH` - Max upload size (bytes)
- `UPLOAD_FOLDER` - Upload directory path
- `DOWNLOAD_FOLDER` - Download directory path
- `TEMP_FOLDER` - Temporary directory path
- `TESSERACT_CMD` - Tesseract executable path
- `LOG_LEVEL` - Logging level (INFO, WARNING, ERROR)
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string

## 🔒 Security Best Practices

### 1. Secrets Management

Use environment variables or secret management services:

```python
# Don't hardcode secrets
SECRET_KEY = os.environ.get('SECRET_KEY')  # ✅ Good

# Never commit secrets to version control
SECRET_KEY = 'hardcoded-secret'  # ❌ Bad
```

### 2. File Upload Security

```python
# Validate file types
ALLOWED_EXTENSIONS = {'pdf'}

# Limit file size
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

# Sanitize filenames
from werkzeug.utils import secure_filename
filename = secure_filename(file.filename)
```

### 3. HTTPS/SSL

Always use HTTPS in production:
- Obtain SSL certificate (Let's Encrypt, etc.)
- Configure Nginx/Apache for SSL
- Redirect HTTP to HTTPS
- Use HSTS header

### 4. Security Headers

Add security headers in Nginx or Flask:

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 5. Rate Limiting

Implement rate limiting:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/merge", methods=["POST"])
@limiter.limit("10 per minute")
def merge_pdfs():
    pass
```

## 📊 Monitoring & Logging

### Application Logging

Configure structured logging:

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        # File handler
        file_handler = RotatingFileHandler(
            'logs/pdfforge.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('PDFForge startup')
```

### Health Check Endpoint

Add health check for monitoring:

```python
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0'
    }), 200
```

### Monitoring Tools

Consider using:
- **Application Performance**: New Relic, DataDog
- **Error Tracking**: Sentry
- **Logging**: ELK Stack, Splunk
- **Uptime Monitoring**: Pingdom, UptimeRobot

## 💾 Backup & Recovery

### Backup Strategy

1. **Application Files**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backups/pdfforge_$DATE.tar.gz /var/www/pdfforge
find /backups -name "pdfforge_*.tar.gz" -mtime +7 -delete
```

2. **Database Backup** (if applicable)
```bash
pg_dump pdfforge > /backups/pdfforge_db_$DATE.sql
```

3. **Automated Backups**
Add to crontab:
```
0 2 * * * /usr/local/bin/backup.sh
```

### Disaster Recovery

1. Document recovery procedures
2. Test backups regularly
3. Store backups off-site
4. Have rollback plan

## 🔧 Troubleshooting

### Common Issues

**Issue: Application won't start**
```bash
# Check logs
sudo journalctl -u pdfforge -n 100
sudo tail -f /var/www/pdfforge/logs/gunicorn_error.log

# Check permissions
ls -la /var/www/pdfforge
```

**Issue: High memory usage**
```bash
# Monitor processes
htop
ps aux | grep gunicorn

# Adjust worker count in gunicorn_config.py
workers = 2  # Reduce if needed
```

**Issue: Slow response times**
```bash
# Check nginx logs
sudo tail -f /var/log/nginx/pdfforge_access.log

# Increase timeouts if needed
```

### Performance Tuning

1. **Worker Configuration**
   - CPU-bound: workers = (2 x CPU cores) + 1
   - I/O-bound: More workers possible

2. **Caching**
   - Implement Redis caching
   - Cache static assets
   - Use CDN for static files

3. **Database Optimization**
   - Add indexes
   - Use connection pooling
   - Optimize queries

## 📚 Additional Resources

- [Flask Deployment Options](https://flask.palletsprojects.com/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 📞 Support

For deployment support:
- GitHub Issues: https://github.com/oscar2song/pdfforge/issues
- Email: oscar2song@gmail.com

---

**Last Updated**: November 2025
**Version**: 2.0.0
