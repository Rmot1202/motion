FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY appilcation/ ./appilcation/

# Create recordings directory
RUN mkdir -p /app/recordings /app/profiles

# Expose port
EXPOSE 8050

# Run the application
CMD ["python", "-m", "appilcation.app"]
