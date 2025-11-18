# Dockerfile
# PDFForge container image
# - Uses Gunicorn to run the Flask app factory
# - Binds to port 8080 (browser-safe)

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps as needed (minimal base; extend if OCR or fonts need OS packages)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     tesseract-ocr \
#     && rm -rf /var/lib/apt/lists/*

# Copy dependency spec first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Create external data/log directories (optional)
RUN mkdir -p /opt/pdf-merge-app/data/uploads \
    /opt/pdf-merge-app/data/downloads \
    /opt/pdf-merge-app/data/temp \
    /opt/pdf-merge-app/logs \
 && chmod -R 755 /opt/pdf-merge-app

# Environment variables
ENV PDF_APP_DATA_DIR=/opt/pdf-merge-app/data \
    FLASK_APP=pdfforge.create_app:create_app \
    PORT=8080

EXPOSE 8080

# Use Gunicorn to serve the Flask app created in app.py (variable: app)
# Tune workers and threads for I/O-bound Flask app
CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "8", "--timeout", "120", "--bind", "0.0.0.0:8080", "app:app"]