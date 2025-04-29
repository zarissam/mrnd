# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy requirements
COPY requirements.txt .

# Install dependencies in a temporary folder
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final clean image
FROM python:3.13-slim

WORKDIR /app

# Copy only installed dependencies
COPY --from=builder /install /usr/local

# Copy your application code
COPY . .

# Expose the app port
EXPOSE 8000

# Command to run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
