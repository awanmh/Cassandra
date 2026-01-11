# Multi-stage build for Cassandra 2.0

# Stage 1: Go Builder (Scanner & Tools)
FROM golang:1.21-alpine AS go-builder

# Install necessary system packages for building
RUN apk add --no-cache git build-base

# Install ProjectDiscovery tools & Dalfox
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
RUN go install -v github.com/hahwul/dalfox/v2@latest

# Stage 2: Python Environment (Final Image)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/go/bin:${PATH}"

# Install system dependencies
# git: for sqlmap
# curl, gnupg: for generic tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright && playwright install-deps

# Create app directory
WORKDIR /app

# Copy Go binaries from builder
COPY --from=go-builder /go/bin/subfinder /usr/local/bin/
COPY --from=go-builder /go/bin/nuclei /usr/local/bin/
COPY --from=go-builder /go/bin/httpx /usr/local/bin/
COPY --from=go-builder /go/bin/dalfox /usr/local/bin/

# Install SQLMap
RUN git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Expose port for Streamlit
EXPOSE 8501

# Command to run (overridden by docker-compose)
CMD ["python", "main.py", "--help"]
