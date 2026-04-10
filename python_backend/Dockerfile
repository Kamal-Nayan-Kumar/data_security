FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/python_backend/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/python_backend/requirements.txt

# Copy the rest of the application
COPY . /app/python_backend/

# Set Python path so `import python_backend.X` works
ENV PYTHONPATH=/app

# Create uploads directory (used by the app)
RUN mkdir -p /app/uploads

# Expose the API port
EXPOSE 8000

# Run migrations and start the server
WORKDIR /app/python_backend
CMD ["bash", "-c", "alembic upgrade head && uvicorn api.app:app --host 0.0.0.0 --port 8000"]
