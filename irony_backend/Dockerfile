FROM python:3.10-slim

# Set a non-root user
RUN useradd -m appuser

WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt .

# Install dependencies without cache (reduces image size)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to the new user
USER appuser

# # Create directory for SSL certificates
# RUN mkdir -p /app/ssl

# # Environment variable to toggle SSL
# ENV SSL_ENABLED=false

# Expose the FastAPI port
EXPOSE 8000

# # Command with conditional SSL configuration
# CMD ["sh", "-c", "if [ \"$SSL_ENABLED\" = \"true\" ]; then uvicorn irony.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile /app/ssl/key.pem --ssl-certfile /app/ssl/cert.pem; else uvicorn irony.main:app --host 0.0.0.0 --port 8000; fi"]

# Start FastAPI with UVicorn in production mode
CMD ["uvicorn", "irony.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]