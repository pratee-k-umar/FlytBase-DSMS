# Setup Guide

Complete installation and configuration guide for the Drone Survey Management System.

## Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend build tools
- **MongoDB** - Database (Atlas or local)
- **Redis** - Channel layer for WebSockets (optional for development)
- **Git** - Version control

### System Requirements

- Windows 10/11, macOS, or Linux
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd FlytBase-DSMS
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd src/dsms
python -m venv venv
```

#### Activate Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

Return to project root and install Node.js dependencies:

```bash
cd ../..  # Back to project root
npm install
```

### 4. Database Configuration

#### MongoDB Atlas (Recommended)

1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Create database user with read/write permissions
4. Whitelist your IP address (or use 0.0.0.0/0 for development)
5. Get connection string

#### Local MongoDB (Alternative)

1. Install MongoDB Community Server
2. Start MongoDB service
3. Use connection string: `mongodb://localhost:27017/dsms`

### 5. Environment Configuration

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dsms?retryWrites=true&w=majority

# Django
DJANGO_SECRET_KEY=your-very-secret-key-here-change-this-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0

# CORS (if frontend on different port)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 6. Initialize Database

Seed the database with sample data:

```bash
python manage.py shell < scripts/seed_data.py
```

Or manually:

```bash
python manage.py shell
>>> from scripts.seed_data import seed_all
>>> seed_all()
>>> exit()
```

## Running the Application

### Development Mode

#### Option 1: Unified Development Server (Recommended)

Run both backend and frontend:

```bash
python dev.py
```

This starts:

- Django API server on `http://localhost:8000`
- Webpack dev server with hot reload

#### Option 2: Separate Servers

**Terminal 1 - Backend:**

```bash
cd src/dsms
venv\Scripts\activate  # Windows
python manage.py runserver 8000
```

**Terminal 2 - Frontend:**

```bash
npm run dev:frontend
```

### Access Application

- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/
- **Admin Interface**: http://localhost:8000/admin/

### Default Login

After seeding, you can use these test drones:

- DRN-0001, DRN-0002, DRN-0003, DRN-0004

## Verification

### Test Backend API

```bash
curl http://localhost:8000/api/fleet/drones/
```

Expected: JSON response with list of drones

### Test Frontend

Navigate to http://localhost:8000 and verify:

- ✅ Dashboard loads with fleet statistics
- ✅ Navigation menu works
- ✅ Drone list displays

### Test Database Connection

```bash
python manage.py shell
```

```python
from dsms.models import Drone
print(Drone.objects.count())  # Should print number of drones
```

## Troubleshooting

### MongoDB Connection Failed

**Issue**: Cannot connect to MongoDB Atlas

**Solutions**:

- Verify connection string in `.env`
- Check network whitelist in MongoDB Atlas
- Ensure password doesn't contain special characters (URL encode if needed)
- Test connection: `mongosh "your-connection-string"`

### Module Not Found Errors

**Issue**: `ModuleNotFoundError: No module named 'django'`

**Solutions**:

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.11+)

### Port Already in Use

**Issue**: `Error: That port is already in use`

**Solutions**:

- Kill existing process: `taskkill /F /IM python.exe` (Windows)
- Use different port: `python manage.py runserver 8001`
- Check what's using port: `netstat -ano | findstr :8000`

### Static Files Not Loading

**Issue**: CSS/JS not loading

**Solutions**:

- Run webpack build: `npm run build`
- Check `STATICFILES_DIRS` in settings
- Clear browser cache
- Verify `dist/` folder exists with built files

### Virtual Environment Issues

**Issue**: Wrong Python version or packages

**Solutions**:

```bash
# Delete and recreate venv
rm -rf venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system design
- Check [API.md](./API.md) for API endpoints
- Review [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment

## Development Tools

### Code Formatting

```bash
# Python
black src/

# JavaScript/TypeScript
npm run lint:fix
```

### Type Checking

```bash
npm run typecheck
```

### Running Tests

```bash
# Backend
cd src/dsms
pytest

# Frontend
npm test
```

## Optional Components

### Redis Setup (for WebSockets)

**Windows:**

- Download Redis for Windows
- Or use WSL: `sudo apt install redis-server`

**macOS:**

```bash
brew install redis
brew services start redis
```

**Linux:**

```bash
sudo apt install redis-server
sudo systemctl start redis
```

### Celery (for background tasks)

```bash
# Start Celery worker
celery -A dsms worker -l info
```

## Environment Variables Reference

| Variable               | Description               | Default                    |
| ---------------------- | ------------------------- | -------------------------- |
| `MONGODB_URI`          | MongoDB connection string | Required                   |
| `DJANGO_SECRET_KEY`    | Django secret key         | Required                   |
| `DJANGO_DEBUG`         | Debug mode                | `True`                     |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts             | `localhost`                |
| `REDIS_URL`            | Redis connection          | `redis://localhost:6379/0` |
| `CORS_ALLOWED_ORIGINS` | CORS origins              | `http://localhost:8000`    |

## Support

If you encounter issues not covered here:

1. Check error logs in console
2. Review [Troubleshooting](#troubleshooting) section
3. Open an issue on GitHub
