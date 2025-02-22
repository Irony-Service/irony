FROM python:3.10-slim

# Set a non-root user
RUN useradd -m appuser

# Install timezone data
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

# Set Asia/Kolkata timezone
ENV TZ=Asia/Kolkata
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

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

# Expose the FastAPI port
EXPOSE 8000

# Start FastAPI with UVicorn in production mode
CMD ["uvicorn", "irony.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]