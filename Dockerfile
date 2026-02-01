# Dockerfile for Render Deployment
# Single unified container for Django API + Frontend

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY src/dsms/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY manage.py ./
COPY static/ ./static/
COPY package.json package-lock.json ./
COPY webpack.config.js tsconfig.json tailwind.config.js postcss.config.js ./

# Install Node dependencies and build frontend
RUN npm ci --production=false && npm run build

# Set Python path and Django settings
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=dsms.conf.settings.production

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Create non-root user
RUN useradd -m -u 1000 dsms && chown -R dsms:dsms /app
USER dsms

# Expose port (Render sets PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Start with gunicorn (with access logs enabled)
CMD gunicorn dsms.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --threads 4 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --access-logformat '"%(m)s %(U)s%(q)s" %(s)s %(b)s %(L)ss'
