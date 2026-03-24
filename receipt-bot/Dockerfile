# Use the official, lightweight, and secure Debian python image
FROM python:3.13-slim

# The recommended way to install uv natively inside a Docker container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation to make Python startup extremely fast
ENV UV_COMPILE_BYTECODE=1
# Prevent hardlinks so Docker volumes dont break uv caches
ENV UV_LINK_MODE=copy

# Copy dependency configuration files first to strictly utilize Docker layer caching
COPY pyproject.toml uv.lock* ./

# Sync dependencies exclusively without developer testing tools to keep image size small
RUN uv sync --frozen --no-install-project --no-dev

# Copy the actual project logic
COPY . .

# Finalize sync locally
RUN uv sync --frozen --no-dev

# Security Best Practice: Never run the container execution as the root user
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Call the local Python binary executed strictly out of the UV generated virtual environment
CMD ["/app/.venv/bin/python", "main.py"]
