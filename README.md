# Drone Survey Management System (DSMS)

A Django-based REST API for managing drone fleet operations, mission planning, and real-time telemetry monitoring.

## Features

- **Mission Planning API** - Define survey areas, configure flight paths, set altitude and speed
- **Real-time Monitoring** - Live drone tracking with WebSocket telemetry
- **Fleet Management API** - Manage drone inventory, status, and availability
- **Analytics API** - Survey statistics and performance metrics
- **Flight Pattern Generator** - Support for waypoint, crosshatch, perimeter, and spiral patterns

## Architecture

This project follows a **Sentry-inspired layered architecture**:

```
src/dsms/
├── models/          # Data models (MongoEngine)
├── api/             # REST API endpoints
│   ├── endpoints/   # One class per resource
│   └── serializers/ # Request/Response schemas
├── services/        # Business logic layer
├── tasks/           # Celery background jobs
├── consumers/       # WebSocket handlers
├── simulator/       # Drone simulation engine
└── utils/           # Shared utilities
```

## Tech Stack

| Layer      | Technology                         |
| ---------- | ---------------------------------- |
| Backend    | Django 5.x + Django REST Framework |
| Database   | MongoDB (MongoEngine ODM)          |
| Real-time  | Django Channels (WebSocket)        |
| Task Queue | Celery + Redis                     |
| API Docs   | OpenAPI / Swagger                  |

## Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier) or local MongoDB
- Redis (local or cloud service like Upstash)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/FlytBase-DSMS.git
cd FlytBase-DSMS

# Install dependencies
make setup
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your MongoDB and Redis connection strings
nano .env
```

Required environment variables:

```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dsms
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

### 3. Run Development Server

```bash
# Start Django API server
make dev
# or
python dev.py
```

- **Unified API & Frontend**: http://localhost:8000/
- **API Endpoints**: http://localhost:8000/api/
- **Health Check**: http://localhost:8000/health/
- **Next.js Dev Server**: http://localhost:3000/ (for development only)

## 🔧 Development Setup

This project uses a **unified development environment** where:

- **Single Command**: `make dev` starts both Django and Next.js servers
- **Dependency Checking**: Automatic validation of Python, Node.js, MongoDB, and Redis
- **Centralized Config**: All configuration files moved to root level
- **Integrated Serving**: Django serves the Next.js build in production

### Available Commands

```bash
# Unified development (recommended)
make dev                    # Start both servers with dependency checks
npm run dev                 # Same as above
python dev.py               # Direct Python script execution

# Individual servers
make dev-back               # Django only
make dev-front              # Next.js only

# Setup and maintenance
make setup                  # Install all dependencies
make test                   # Run all tests
make lint                   # Run linters
make format                 # Format code
make clean                  # Clean cache files
```

### Configuration Files

All configuration is now centralized at the root level:

```
config/
├── settings/               # Django settings
│   ├── base.py
│   ├── development.py
│   └── production.py
└── urls.py                 # URL routing

# Next.js configs (root level)
next.config.ts
tsconfig.json
postcss.config.mjs
components.json
eslint.config.mjs
```

## 📚 API Endpoints

### Missions

| Method | Endpoint                     | Description         |
| ------ | ---------------------------- | ------------------- |
| GET    | `/api/missions/`             | List all missions   |
| POST   | `/api/missions/`             | Create mission      |
| GET    | `/api/missions/<id>/`        | Get mission details |
| PATCH  | `/api/missions/<id>/`        | Update mission      |
| DELETE | `/api/missions/<id>/`        | Delete mission      |
| POST   | `/api/missions/<id>/start/`  | Start mission       |
| POST   | `/api/missions/<id>/pause/`  | Pause mission       |
| POST   | `/api/missions/<id>/resume/` | Resume mission      |
| POST   | `/api/missions/<id>/abort/`  | Abort mission       |

### Fleet

| Method | Endpoint                  | Description       |
| ------ | ------------------------- | ----------------- |
| GET    | `/api/fleet/drones/`      | List all drones   |
| POST   | `/api/fleet/drones/`      | Register drone    |
| GET    | `/api/fleet/drones/<id>/` | Get drone details |
| GET    | `/api/fleet/stats/`       | Fleet statistics  |

### WebSocket

```
ws://localhost:8000/ws/missions/<mission_id>/telemetry/
```

## 🧪 Testing

```bash
# Run tests
make test

# Run linter
make lint

# Format code
make format
```

## 🚢 Deployment

### Unified Deployment (Recommended)

Since the frontend is now served by Django, you only need to deploy the Django application:

1. **Build the frontend for production:**

    ```bash
    npm run build
    ```

2. **Deploy Django application** (Render, Railway, etc.):
    - The Django app will serve both API and frontend
    - Set environment variables from `.env.example`
    - Static files are automatically collected during deployment

### Separate Deployment (Alternative)

If you prefer separate deployments:

#### Backend (Render)

1. Create new Web Service on Render
2. Connect GitHub repository
3. Set environment variables from `.env.example`
4. Deploy

#### Frontend (Vercel)

1. Import project to Vercel
2. Set root directory to `src/static`
3. Configure API proxy to your backend URL
4. Deploy

## 📖 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Demo

[Watch the demo video](link-to-demo)

## License

MIT License

---

Built for the FlytBase Design Challenge
