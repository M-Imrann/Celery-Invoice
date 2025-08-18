# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for Pillow/ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    tcl-dev tk-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# If you have a requirements.txt, copy & install first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Now copy the project
COPY . /app

# Create media directory (for invoices & user images)
RUN mkdir -p /app/media

EXPOSE 8000

# Default command is set in docker-compose for each service
