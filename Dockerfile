FROM python:3.11-slim

# Create a non-root user for security (Principle of Least Privilege)
RUN groupadd -r sentinel && useradd -r -m -g sentinel sentinel

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create necessary directories and set ownership before switching user
RUN mkdir -p /app /logs /temp && \
    chown -R sentinel:sentinel /app /logs /temp

# Set working directory
WORKDIR /app

# Switch to non-root user
USER sentinel

# Copy requirements and install them (user mode)
COPY --chown=sentinel:sentinel requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Ensure the local user bin is in PATH
ENV PATH="/home/sentinel/.local/bin:${PATH}"

# Copy the rest of the application code
COPY --chown=sentinel:sentinel . .

# Default command to run the main application
CMD ["python", "src/main.py"]
