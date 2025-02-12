FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for SSL certificates
RUN mkdir -p /app/ssl

# Environment variable to toggle SSL
ENV SSL_ENABLED=false

EXPOSE 8000

# Command with conditional SSL configuration
CMD ["sh", "-c", "if [ \"$SSL_ENABLED\" = \"true\" ]; then uvicorn irony.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile /app/ssl/key.pem --ssl-certfile /app/ssl/cert.pem; else uvicorn irony.main:app --host 0.0.0.0 --port 8000; fi"]