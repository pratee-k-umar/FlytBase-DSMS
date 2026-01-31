# Deployment Guide

Production deployment guide for the Drone Survey Management System.

## Deployment Options

1. **Platform as a Service (Easiest)** - Render, Railway, Heroku
2. **Cloud Platform (Production)** - AWS, Azure, Google Cloud
3. **Traditional VPS** - DigitalOcean, Linode, Vultr
4. **Docker Container** - Any Docker-compatible host
5. **Vercel** - Frontend only (requires separate backend)

## Prerequisites

### Required Services

- **MongoDB Atlas** (recommended) or self-hosted MongoDB
- **Redis** instance for WebSocket channel layer
- **Domain name** (optional but recommended)
- **SSL Certificate** (Let's Encrypt recommended)

### System Requirements

- **Ubuntu 20.04 LTS** or similar Linux distribution
- **4GB RAM** minimum (8GB recommended)
- **2 CPU cores** minimum
- **20GB disk space**
- **Python 3.11+**
- **Node.js 18+**
- **Nginx** (reverse proxy)
- **Supervisor** or **systemd** (process management)

---

## Option 1: Render (Recommended for Beginners) ⭐

**Render is the easiest option with free tier available. Perfect for small to medium applications.**

### Prerequisites

- GitHub account with your code pushed
- MongoDB Atlas account (free tier)
- Render account (free at https://render.com)

### Step 1: Prepare Your Repository

**Create `render.yaml` in project root:**

```yaml
services:
    # Web Service (Django)
    - type: web
      name: dsms-web
      env: python
      region: oregon
      plan: starter # Free tier or upgrade to paid
      buildCommand: |
          pip install -r src/dsms/requirements.txt
          npm install
          npm run build
      startCommand: |
          cd src/dsms && gunicorn dsms.wsgi:application --bind 0.0.0.0:$PORT
      envVars:
          - key: PYTHON_VERSION
            value: 3.11.0
          - key: DJANGO_SECRET_KEY
            generateValue: true
          - key: DJANGO_DEBUG
            value: False
          - key: DJANGO_ALLOWED_HOSTS
            value: .onrender.com
          - key: MONGODB_URI
            sync: false # Set manually in Render dashboard
          - key: REDIS_URL
            fromService:
                name: dsms-redis
                type: redis
                property: connectionString

    # Redis (for WebSocket channel layer)
    - type: redis
      name: dsms-redis
      region: oregon
      plan: starter # Free tier
      maxmemoryPolicy: noeviction
```

**Update `src/dsms/requirements.txt` - add Gunicorn:**

```txt
gunicorn>=21.2
```

### Step 2: Configure Django Settings

**Create `src/dsms/conf/settings/production.py`:**

```python
from .base import *
import os

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {}  # MongoDB via MongoEngine

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS
CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
    'https://dsms-web.onrender.com',
]
```

**Update `manage.py` to use production settings:**

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
    'dsms.conf.settings.production' if os.getenv('RENDER')
    else 'dsms.conf.settings.development')
```

### Step 3: Deploy on Render

**Via Render Dashboard:**

1. **Sign up** at https://render.com
2. **Connect GitHub** repository
3. **Create Web Service**:
    - Click "New +" → "Web Service"
    - Connect your GitHub repo
    - Name: `dsms-web`
    - Region: Oregon (or closest)
    - Branch: `main`
    - Build Command: `pip install -r src/dsms/requirements.txt && npm install && npm run build`
    - Start Command: `cd src/dsms && gunicorn dsms.wsgi:application --bind 0.0.0.0:$PORT`
    - Plan: Free (or Starter $7/month)

4. **Add Environment Variables** in Render dashboard:

    ```
    PYTHON_VERSION=3.11.0
    DJANGO_SECRET_KEY=(auto-generated)
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS=.onrender.com
    MONGODB_URI=your-mongodb-atlas-connection-string
    ```

5. **Create Redis Instance**:
    - Click "New +" → "Redis"
    - Name: `dsms-redis`
    - Plan: Free
    - Copy connection string to `REDIS_URL` env var

6. **Deploy**: Render will automatically deploy on push to main branch

**Via Render Blueprint (render.yaml):**

1. Push `render.yaml` to your repo
2. In Render dashboard: "New +" → "Blueprint"
3. Connect repo and select `render.yaml`
4. Set `MONGODB_URI` environment variable
5. Deploy

### Step 4: Configure Custom Domain (Optional)

1. In Render dashboard, go to your web service
2. Click "Settings" → "Custom Domain"
3. Add your domain: `app.yourdomain.com`
4. Add CNAME record in your DNS:
    ```
    CNAME  app  dsms-web.onrender.com
    ```
5. SSL certificate is automatically provisioned

### Render Advantages

- ✅ Free tier available (with limitations)
- ✅ Automatic SSL certificates
- ✅ Auto-deploy on git push
- ✅ Easy Redis integration
- ✅ Zero-downtime deploys
- ✅ Automatic HTTPS redirect
- ✅ Built-in health checks

### Render Limitations

- Free tier spins down after 15 minutes of inactivity (cold starts)
- 750 hours/month on free tier
- Limited build minutes on free tier

### Render Pricing

- **Free**: 750 hours/month, spins down after inactivity
- **Starter ($7/month)**: Always on, no cold starts
- **Standard ($25/month)**: More resources, better performance

---

## Option 2: Vercel (Frontend Only)

**⚠️ Note: Vercel is designed for frontend/static sites. For this full-stack Django app, you'll need to:**

1. Deploy backend separately (Render/Railway/Heroku)
2. Deploy frontend React app on Vercel
3. Configure CORS properly

### Not Recommended for This Project

Vercel works best for:

- Next.js applications
- Static sites
- Serverless functions

For a Django + React monorepo like DSMS, **Render or Railway are better choices** as they handle the full stack in one deployment.

### If You Still Want to Use Vercel for Frontend

**1. Split the application:**

- Deploy Django backend on Render/Railway
- Deploy React frontend on Vercel separately

**2. Configure frontend build:**

Create `vercel.json`:

```json
{
    "buildCommand": "npm run build",
    "outputDirectory": "dist",
    "framework": null,
    "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

**3. Update API base URL:**

```typescript
// static/app/services/api.ts
const API_BASE_URL =
    process.env.VITE_API_URL || "https://dsms-api.onrender.com";
```

**4. Deploy:**

```bash
vercel --prod
```

This approach is **more complex** and requires managing two separate deployments.

---

## Option 3: Railway (Similar to Render)

**Railway is another excellent PaaS option, very similar to Render.**

### Quick Deploy on Railway

1. **Sign up** at https://railway.app
2. **Create New Project** → "Deploy from GitHub"
3. **Connect repository**
4. **Add Redis**: Click "New" → "Database" → "Redis"
5. **Configure Web Service**:
    ```
    Build Command: pip install -r src/dsms/requirements.txt && npm install && npm run build
    Start Command: cd src/dsms && gunicorn dsms.wsgi:application --bind 0.0.0.0:$PORT
    ```
6. **Add Environment Variables**:
    ```
    MONGODB_URI=your-connection-string
    DJANGO_SECRET_KEY=(generate random key)
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS=.railway.app
    ```
7. **Deploy**: Automatic on push to main

### Railway vs Render

| Feature     | Railway                 | Render                 |
| ----------- | ----------------------- | ---------------------- |
| Free Tier   | $5 credit/month         | 750 hours/month        |
| Cold Starts | No on paid plans        | No on paid plans       |
| Redis       | Included                | Separate service       |
| Pricing     | Usage-based (~$5-20/mo) | Fixed tiers ($7-25/mo) |
| UI/UX       | Modern, simple          | Clean, intuitive       |

**Recommendation**: Both are excellent. Choose based on preference:

- **Railway**: If you prefer usage-based pricing
- **Render**: If you prefer predictable fixed pricing

---

## Option 4: Cloud Platform Deployment (AWS Example)

### Step 1: Provision Infrastructure

**AWS Services Required:**

- EC2 instance (t3.medium or larger)
- MongoDB Atlas (free tier or paid)
- ElastiCache Redis (optional, can use EC2)
- S3 bucket (for static files)
- Route53 (DNS)
- Certificate Manager (SSL)

**Launch EC2 Instance:**

```bash
# Ubuntu 20.04 LTS
# Instance type: t3.medium (2 vCPU, 4GB RAM)
# Security Group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

### Step 2: Server Setup

**Connect to server:**

```bash
ssh ubuntu@your-server-ip
```

**Update system:**

```bash
sudo apt update && sudo apt upgrade -y
```

**Install dependencies:**

```bash
# Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Nginx
sudo apt install nginx -y

# Supervisor
sudo apt install supervisor -y

# Git
sudo apt install git -y

# Redis (optional if not using ElastiCache)
sudo apt install redis-server -y
```

### Step 3: Deploy Application

**Clone repository:**

```bash
cd /opt
sudo git clone <your-repository-url> dsms
sudo chown -R ubuntu:ubuntu dsms
cd dsms
```

**Setup backend:**

```bash
cd /opt/dsms/src/dsms
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # WSGI server
```

**Build frontend:**

```bash
cd /opt/dsms
npm install
npm run build
```

**Create production environment file:**

```bash
cat > /opt/dsms/.env << EOF
# Production Environment
DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dsms?retryWrites=true&w=majority

# Redis (ElastiCache or local)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
EOF
```

### Step 4: Configure Gunicorn

**Create Gunicorn config:**

```bash
sudo nano /etc/supervisor/conf.d/dsms-gunicorn.conf
```

```ini
[program:dsms-gunicorn]
directory=/opt/dsms
command=/opt/dsms/src/dsms/venv/bin/gunicorn dsms.wsgi:application --bind 127.0.0.1:8000 --workers 4 --timeout 120
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dsms/gunicorn.log
environment=PATH="/opt/dsms/src/dsms/venv/bin"
```

### Step 5: Configure Daphne (for WebSockets)

**Create Daphne config:**

```bash
sudo nano /etc/supervisor/conf.d/dsms-daphne.conf
```

```ini
[program:dsms-daphne]
directory=/opt/dsms
command=/opt/dsms/src/dsms/venv/bin/daphne -b 127.0.0.1 -p 8001 dsms.asgi:application
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dsms/daphne.log
environment=PATH="/opt/dsms/src/dsms/venv/bin"
```

### Step 6: Configure Nginx

**Create Nginx config:**

```bash
sudo nano /etc/nginx/sites-available/dsms
```

```nginx
upstream django {
    server 127.0.0.1:8000;
}

upstream daphne {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /opt/dsms/dist/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # API and main app
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/dsms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: SSL Certificate

**Install Certbot:**

```bash
sudo apt install certbot python3-certbot-nginx -y
```

**Get certificate:**

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Step 8: Start Services

**Create log directory:**

```bash
sudo mkdir -p /var/log/dsms
sudo chown ubuntu:ubuntu /var/log/dsms
```

**Start services:**

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start dsms-gunicorn
sudo supervisorctl start dsms-daphne
```

**Check status:**

```bash
sudo supervisorctl status
```

### Step 9: Verify Deployment

**Test API:**

```bash
curl https://yourdomain.com/api/fleet/drones/
```

**Test WebSocket:**

```javascript
const ws = new WebSocket(
    "wss://yourdomain.com/ws/missions/MSN-0001/telemetry/",
);
```

---

## Option 5: Docker Deployment

### Create Dockerfile

**Backend Dockerfile:**

```dockerfile
# /opt/dsms/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY src/dsms/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn daphne

# Copy application
COPY . .

# Collect static files
RUN mkdir -p /app/staticfiles

# Expose port
EXPOSE 8000

# Start command (override in docker-compose)
CMD ["gunicorn", "dsms.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Create docker-compose.yml

```yaml
version: "3.8"

services:
    redis:
        image: redis:7-alpine
        restart: always
        ports:
            - "6379:6379"
        volumes:
            - redis_data:/data

    web:
        build: .
        command: gunicorn dsms.wsgi:application --bind 0.0.0.0:8000 --workers 4
        volumes:
            - .:/app
            - static_volume:/app/staticfiles
        ports:
            - "8000:8000"
        env_file:
            - .env.production
        depends_on:
            - redis
        restart: always

    daphne:
        build: .
        command: daphne -b 0.0.0.0 -p 8001 dsms.asgi:application
        volumes:
            - .:/app
        ports:
            - "8001:8001"
        env_file:
            - .env.production
        depends_on:
            - redis
        restart: always

    nginx:
        image: nginx:alpine
        volumes:
            - ./nginx.conf:/etc/nginx/nginx.conf
            - static_volume:/app/staticfiles
            - ./certbot/conf:/etc/letsencrypt
            - ./certbot/www:/var/www/certbot
        ports:
            - "80:80"
            - "443:443"
        depends_on:
            - web
            - daphne
        restart: always

volumes:
    redis_data:
    static_volume:
```

### Deploy with Docker

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Option 6: Heroku (Alternative PaaS)

### Heroku Setup

**Install Heroku CLI:**

```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

**Login and create app:**

```bash
heroku login
heroku create your-app-name
```

**Add buildpacks:**

```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs
```

**Add Redis:**

```bash
heroku addons:create heroku-redis:hobby-dev
```

**Set environment variables:**

```bash
heroku config:set DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
heroku config:set DJANGO_DEBUG=False
heroku config:set DJANGO_ALLOWED_HOSTS=your-app-name.herokuapp.com
heroku config:set MONGODB_URI=your-mongodb-atlas-uri
```

### Create Procfile

```procfile
web: cd src/dsms && gunicorn dsms.wsgi:application --bind 0.0.0.0:$PORT
worker: cd src/dsms && daphne dsms.asgi:application --port $PORT --bind 0.0.0.0
```

### Deploy

```bash
git push heroku main
heroku ps:scale web=1 worker=1
heroku logs --tail
```

---

## Post-Deployment Tasks

### 1. Database Seeding

```bash
# SSH to server
ssh ubuntu@your-server-ip

# Activate venv and seed data
cd /opt/dsms
source src/dsms/venv/bin/activate
python manage.py shell < scripts/seed_data.py
```

### 2. Setup Monitoring

**Install monitoring tools:**

```bash
# Sentry for error tracking
pip install sentry-sdk

# Add to Django settings
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

**System monitoring:**

```bash
# Install monitoring agent (e.g., DataDog, New Relic)
# Configure alerts for:
# - CPU usage > 80%
# - Memory usage > 90%
# - Disk space < 10%
# - Response time > 2s
```

### 3. Setup Backups

**MongoDB backups:**

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mongodump --uri="$MONGODB_URI" --out=/backups/mongo_$DATE
# Upload to S3
aws s3 cp /backups/mongo_$DATE s3://your-bucket/backups/ --recursive
```

**Schedule with cron:**

```bash
crontab -e
# Add: 0 2 * * * /opt/dsms/scripts/backup.sh
```

### 4. Enable HTTPS

Already covered in Nginx config with Let's Encrypt.

### 5. Configure Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## Performance Optimization

### 1. Enable Caching

**Redis caching in Django:**

```python
# settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
    }
}
```

### 2. Database Indexing

**Add MongoDB indexes:**

```python
# In models
class Mission(BaseDocument):
    meta = {
        'indexes': [
            'mission_id',
            'status',
            'assigned_drone_id',
            ('site_name', 'status'),
        ]
    }
```

### 3. CDN for Static Files

**Use AWS CloudFront or Cloudflare:**

```python
# settings/production.py
STATIC_URL = 'https://cdn.yourdomain.com/static/'
```

### 4. Gunicorn Workers

```bash
# Calculate workers: (2 × CPU cores) + 1
# For 4 cores: 9 workers
--workers 9
```

---

## Monitoring & Maintenance

### Application Logs

```bash
# View Gunicorn logs
sudo tail -f /var/log/dsms/gunicorn.log

# View Daphne logs
sudo tail -f /var/log/dsms/daphne.log

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

**Add health check endpoint:**

```python
# urls.py
path('health/', health_check, name='health'),
```

**Monitor with:**

- UptimeRobot
- Pingdom
- AWS Route53 health checks

### Auto-scaling (AWS)

Configure Auto Scaling Group:

- Scale up when CPU > 70%
- Scale down when CPU < 30%
- Min instances: 2
- Max instances: 10

---

## Security Checklist

- [x] HTTPS enabled with valid SSL certificate
- [x] `DEBUG=False` in production
- [x] Strong `SECRET_KEY` generated
- [x] MongoDB authentication enabled
- [x] Redis password set
- [x] Firewall configured (UFW/Security Groups)
- [x] Regular security updates scheduled
- [x] CORS properly configured
- [x] Environment variables secured
- [x] SSH key-based authentication only
- [x] Fail2ban installed (optional)
- [x] Rate limiting configured (optional)

---

## Rollback Procedure

```bash
# SSH to server
ssh ubuntu@your-server-ip

# Pull previous version
cd /opt/dsms
git fetch --all
git checkout <previous-commit-hash>

# Rebuild frontend
npm run build

# Restart services
sudo supervisorctl restart dsms-gunicorn
sudo supervisorctl restart dsms-daphne
```

---

## Cost Estimation (Monthly)

### Render (Recommended for Beginners) ⭐

- **Free Tier**: $0 (with cold starts)
    - Web Service: Free (750 hours)
    - Redis: Free
    - MongoDB Atlas M0: Free
- **Starter Tier**: $7-15/month
    - Web Service: $7/month (always on)
    - Redis: Free
    - MongoDB Atlas M0: Free

### Railway

- **Hobby**: ~$5-10/month (usage-based)
    - $5 free credit per month
    - Web Service: ~$5-10
    - Redis: Included
    - MongoDB Atlas M0: Free
- **Pro**: ~$20/month for better limits

### AWS Deployment (Production Scale)

- EC2 t3.medium: ~$30
- MongoDB Atlas M10: ~$60
- ElastiCache (optional): ~$15
- Data transfer: ~$10
- **Total: ~$115/month**

### Heroku

- Dyno (Hobby): $7
- Redis: $15
- MongoDB Atlas M0: Free
- **Total: ~$22/month**

### DigitalOcean

- Droplet (4GB): $24
- MongoDB Atlas M0: Free
- Redis on droplet: Free
- **Total: ~$24/month**

### Vercel (Frontend Only)

- Free tier available
- Pro: $20/month (requires separate backend)
- Not recommended for this full-stack app

**Best Value**:

- **For Development/Testing**: Render Free Tier
- **For Small Production**: Render Starter ($7/month) or Railway (~$10/month)
- **For Scale**: AWS (~$115/month) with auto-scaling

---

## Troubleshooting Production Issues

### 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo supervisorctl status dsms-gunicorn

# Check logs
sudo tail -f /var/log/dsms/gunicorn.log

# Restart
sudo supervisorctl restart dsms-gunicorn
```

### WebSocket Connection Failed

```bash
# Check Daphne
sudo supervisorctl status dsms-daphne

# Verify Redis
redis-cli ping

# Check Nginx config
sudo nginx -t
```

### High Memory Usage

```bash
# Check processes
htop

# Restart services
sudo supervisorctl restart all

# Consider increasing instance size
```

---

## CI/CD Pipeline (GitHub Actions)

**Create `.github/workflows/deploy.yml`:**

```yaml
name: Deploy to Production

on:
    push:
        branches: [main]

jobs:
    deploy:
        runs-on: ubuntu-latest

        steps:
            - uses: actions/checkout@v3

            - name: Deploy to server
              uses: appleboy/ssh-action@master
              with:
                  host: ${{ secrets.SERVER_HOST }}
                  username: ${{ secrets.SERVER_USER }}
                  key: ${{ secrets.SSH_PRIVATE_KEY }}
                  script: |
                      cd /opt/dsms
                      git pull origin main
                      source src/dsms/venv/bin/activate
                      pip install -r src/dsms/requirements.txt
                      npm install
                      npm run build
                      sudo supervisorctl restart all
```

---

## Support & Resources

- **MongoDB Atlas**: https://cloud.mongodb.com
- **Let's Encrypt**: https://letsencrypt.org
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Gunicorn Documentation**: https://docs.gunicorn.org
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/

For issues, check logs first, then refer to troubleshooting section or open a GitHub issue.
