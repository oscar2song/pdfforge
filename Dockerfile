# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy application code
COPY app/ ./app/
COPY requirements.txt .

# Create external data directory
RUN mkdir -p /opt/pdf-merge-app/data/uploads
RUN mkdir -p /opt/pdf-merge-app/data/downloads
RUN mkdir -p /opt/pdf-merge-app/data/temp
RUN mkdir -p /opt/pdf-merge-app/logs

# Set permissions
RUN chmod -R 755 /opt/pdf-merge-app

# Install dependencies
RUN pip install -r requirements.txt

# Set environment variables
ENV PDF_APP_DATA_DIR=/opt/pdf-merge-app/data
ENV FLASK_APP=app.main:create_app

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:create_app()"]