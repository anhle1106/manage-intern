FROM python:3.11-slim

WORKDIR /app

# Security: Create non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

# Install binary wheels fast
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assign ownership to appuser
COPY --chown=appuser:appgroup . /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
