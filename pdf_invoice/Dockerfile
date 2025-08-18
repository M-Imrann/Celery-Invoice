# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


WORKDIR /app

# If you have a requirements.txt, copy & install first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Now copy the project
COPY . /app

# Create media directory (for invoices & user images)
RUN mkdir -p /app/media

EXPOSE 8000
