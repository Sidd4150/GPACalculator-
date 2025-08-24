FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY backend/ .

# Note: Port is dynamic (set via PORT env var in production, defaults to 8000 locally)

# Run the application using the main.py logic for port handling
CMD ["python", "-m", "app.main"]