# Stage 1: Build dependencies
FROM python:3.14-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final minimal runner image
FROM python:3.14-slim AS runner

# Create a non-root user for security (Principle of Least Privilege)
RUN groupadd -r sentinel && useradd -r -m -g sentinel sentinel

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create necessary directories and set ownership before switching user
RUN mkdir -p /app /app/chroma_db /logs /temp /home/sentinel/.gunicorn && \
    chown -R sentinel:sentinel /app /app/chroma_db /logs /temp /home/sentinel/.gunicorn

# Copy installed packages from builder to standard system path
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Switch to non-root user
USER sentinel

# Copy the rest of the application code
COPY --chown=sentinel:sentinel . .

# Default command to run the main application
CMD ["python", "src/main.py"]
