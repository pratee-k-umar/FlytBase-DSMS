# Setup Guide

Complete installation and configuration guide for the Drone Survey Management System.

## Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **Node.js 18+ and npm** - Frontend build tools
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
git clone https://github.com/yourusername/FlytBase-DSMS.git
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

This will install all required packages including:

- React 18 + TypeScript
- shadcn/ui components
- Tailwind CSS
- React Query
- Leaflet for maps
- Webpack build tools

### 4. Database Configuration

#### MongoDB Atlas (Recommended)

1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (M0 Free tier is sufficient)
3. Create database user with read/write permissions
4. Add your IP address to IP Access List (or use 0.0.0.0/0 for development)
5. Get connection string from Connect → Connect your application

#### Local MongoDB (Alternative)

1. Install MongoDB Community Server
2. Start MongoDB service:

    ```bash
    # Windows
    net start MongoDB

    # macOS (with Homebrew)
    brew services start mongodb-community

    # Linux
    sudo systemctl start mongod
    ```

3. Use connection string: `mongodb://localhost:27017/dsms`

### 5. Environment Configuration

Create `.env` file in project root:

```bash
# Copy from example (if available)
cp .env.example .env

# Or create new file
touch .env
```

Edit `.env` with your settings:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dsms?retryWrites=true&w=majority

# Redis Configuration (optional for development)
REDIS_URL=redis://localhost:6379

# Django Configuration
SECRET_KEY=your-very-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Django Settings Module
DJANGO_SETTINGS_MODULE=dsms.conf.settings.development
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0

# CORS (if frontend on different port)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 6. Seed Initial Data

#### Load DJI Drone Fleet

The project includes a seed script to populate your database with realistic DJI drone models:

```bash
python scripts/seed_drone_fleet.py
```

This will create:

- **12 DJI drone models** (Mavic 4/3 Pro, Air 3S, Mini 5/4/3/2 SE, Flip, Neo 2/Neo, Avata 2, Inspire 3)
- **30-45 drones per base** with realistic specifications
- **Category-based naming** (Alpha/Beta for Mavic, Sky/Cloud for Air, etc.)
- **Drone images** linked from `/static/drone-gallery/`
- **Varied specifications** based on drone category (flight time, speed, payload)

#### Create Sample Bases (Optional)

You can create bases manually through the UI or using the Django shell:

```bash
cd src/dsms
python manage.py shell
```

```python
from dsms.models.drone import DroneBase

base = DroneBase(
    base_id="BASE-0001",
    name="Central Operations",
    lat=12.9716,
    lng=77.5946,
    capacity=50,
    status="active"
)
base.save()
```

## Running the Application

### Development Mode

#### Option 1: Unified Development Script

Run both backend and frontend:

```bash
python dev.py
```

This starts:

- Django API server on `http://localhost:8000`
- Webpack dev server on `http://localhost:5173` with hot reload

#### Option 2: Separate Servers

**Terminal 1 - Backend:**

```bash
cd src/dsms
# Activate virtual environment first
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run Django server
python manage.py runserver 8000
```

**Terminal 2 - Frontend:**

```bash
# From project root
npm run dev:frontend
```

### Access Application

- **Main Application (Dev)**: http://localhost:5173
- **API Backend**: http://localhost:8000/api/
- **Health Check**: http://localhost:8000/health/
- **Production Build**: http://localhost:8000 (after running `npm run build`)

### Application Features

After seeding, you can:

- **View Bases**: Navigate to `/bases` to see all operational bases on the map
- **Manage Drones**: Go to `/drones` to see your DJI fleet with images and specs
- **Create Missions**: Use `/mission/planner` to plan new survey missions
- **Monitor Live**: Track active missions at `/mission/monitor`
- **View Analytics**: Check fleet statistics at `/analytics`

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
