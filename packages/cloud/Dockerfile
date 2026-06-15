FROM python:3.11-slim

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install cloud package + deps
COPY packages/cloud/pyproject.toml packages/cloud/
WORKDIR /app/packages/cloud
RUN pip install --no-cache-dir .

# Copy source
COPY packages/cloud/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]