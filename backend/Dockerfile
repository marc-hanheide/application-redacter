FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create upload directory
RUN mkdir -p /tmp/uploads

# Expose port
EXPOSE 5000

# Environment variable for Python to show logs immediately
ENV PYTHONUNBUFFERED=1

# Run with gunicorn with logging to stdout
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "300", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
