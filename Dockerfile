# Multi-stage Dockerfile for Azure DevOps Sprint MCP Server
# Optimized for production deployment to Azure Container Registry (ACR)

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Set metadata
LABEL maintainer="noreply@example.com"
LABEL description="Azure DevOps Sprint MCP Server"
LABEL version="2.1"

# Install Azure CLI for user credential support
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Azure-specific environment variables
    PORT=8000 \
    # Disable Azure CLI telemetry and logging in containers
    AZURE_CORE_COLLECT_TELEMETRY=false \
    AZURE_CORE_NO_COLOR=true \
    AZURE_CORE_ONLY_SHOW_ERRORS=true \
    # Set Azure DevOps cache to writable location
    AZURE_DEVOPS_CACHE_DIR=/app/cache/.azure-devops

# Create non-root user for security with home directory
RUN groupadd -r mcpuser && \
    useradd -r -g mcpuser -u 1000 -m -d /home/mcpuser mcpuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src/ ./src/
COPY README.md ./

# Create directories for logs and cache, ensure home directory ownership
RUN mkdir -p /app/logs /app/cache && \
    chown -R mcpuser:mcpuser /app && \
    chown -R mcpuser:mcpuser /home/mcpuser

# Switch to non-root user
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose port (configurable via PORT env var)
EXPOSE ${PORT}

# Default command (can be overridden)
CMD ["python", "-m", "src.server"]
