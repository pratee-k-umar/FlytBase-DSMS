# Drone Survey Management System (DSMS)

A full-stack drone fleet management platform with Django REST API backend and React TypeScript frontend. Monitor your drone fleet, plan missions, track real-time telemetry, and manage multiple operational bases.

## Features

### Core Functionality

- **Base Management** - Create and manage operational bases with map visualization
- **Drone Fleet Management** - Add, monitor, and control DJI drone fleet with detailed specifications
- **Mission Planning** - Define survey areas, configure flight paths with multiple pattern types
- **Real-time Mission Monitoring** - Live drone tracking with WebSocket telemetry
- **Analytics Dashboard** - Fleet statistics, mission history, and performance metrics
- **Flight Pattern Generator** - Support for waypoint, crosshatch, perimeter, and spiral patterns

### User Interface

- **Interactive Map** - Leaflet-based map with base locations and drone positioning
- **Real-time Updates** - React Query for efficient data fetching and caching
- **Responsive Design** - Tailwind CSS with shadcn/ui components
- **Dark Mode Support** - Clean, modern interface with neutral color scheme

## Architecture

This project follows a **layered full-stack architecture**:

```
FlytBase-DSMS/
├── src/dsms/                    # Django Backend
│   ├── models/                  # MongoDB models (MongoEngine)
│   ├── api/                     # REST API endpoints
│   │   ├── endpoints/           # Resource endpoints
│   │   └── serializers/         # Request/Response schemas
│   ├── services/                # Business logic layer
│   │   ├── fleet_service.py     # Drone fleet operations
│   │   ├── mission_service.py   # Mission management
│   │   ├── path_generator.py    # Flight path algorithms
│   │   └── analytics_service.py # Statistics and metrics
│   ├── tasks/                   # Celery background jobs
│   ├── consumers/               # WebSocket handlers
│   ├── simulator/               # Drone physics simulation
│   └── utils/                   # Shared utilities
├── static/app/                  # React Frontend
│   ├── pages/                   # Main application pages
│   │   ├── Bases.tsx            # Base management (default)
│   │   ├── Drone.tsx            # Drone fleet dashboard
│   │   ├── Missions.tsx         # Mission list and control
│   │   ├── MissionPlanner.tsx   # Create new missions
│   │   ├── LiveMonitor.tsx      # Real-time mission tracking
│   │   └── Analytics.tsx        # Statistics and charts
│   ├── components/              # Reusable UI components
│   │   ├── common/              # Layout, navigation
│   │   └── ui/                  # shadcn/ui components
│   ├── services/                # API client services
│   ├── types/                   # TypeScript interfaces
│   └── hooks/                   # React custom hooks
└── scripts/                     # Utility scripts
    ├── seed_drone_fleet.py      # Load DJI drone fleet data
    └── test_api.py              # API testing utilities
```

## Tech Stack

| Layer      | Technology                         |
| ---------- | ---------------------------------- |
| Frontend   | React 18 + TypeScript + Vite       |
| UI Library | shadcn/ui + Tailwind CSS           |
| State      | React Query + Zustand              |
| Maps       | Leaflet + React Leaflet            |
| Backend    | Django 6.x + Django REST Framework |
| Database   | MongoDB (MongoEngine ODM)          |
| Real-time  | Django Channels (WebSocket)        |
| Task Queue | Celery + Redis                     |
| Build      | Webpack 5                          |

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- MongoDB Atlas account (free tier) or local MongoDB
- Redis (local or cloud service)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/FlytBase-DSMS.git
cd FlytBase-DSMS

# Install Python dependencies
cd src/dsms
pip install -r requirements.txt

# Install Node.js dependencies
cd ../..
npm install
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dsms

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Django Settings Module
DJANGO_SETTINGS_MODULE=dsms.conf.settings.development
```

### 3. Seed Initial Data

```bash
# Load DJI drone fleet data
python scripts/seed_drone_fleet.py
```

This will populate your database with:

- 12 DJI drone models (Mavic 4/3 Pro, Air 3S, Mini series, Flip, Neo, Avata 2, Inspire 3)
- 30-45 drones per base with realistic specifications
- Drone images from static/drone-gallery

### 4. Run Development Servers

**Backend (Django):**

```bash
cd src/dsms
python manage.py runserver
```

**Frontend (Webpack Dev Server):**

```bash
npm run dev:frontend
```

**Or use the unified dev script:**

```bash
python dev.py
```

Access the application:

- **Frontend**: http://localhost:5173/ (dev) or http://localhost:8000/ (production)
- **API**: http://localhost:8000/api/
- **Health Check**: http://localhost:8000/health/

## 🔧 Development Commands

### Build Commands

```bash
# Build frontend for production
npm run build

# Type checking
npm run typecheck

# Linting
npm run lint
npm run lint:fix
```

### Database Seeding

```bash
# Seed drone fleet with DJI models
python scripts/seed_drone_fleet.py

# Test API endpoints
python scripts/test_api.py
```

## 📚 API Endpoints

### Bases

| Method | Endpoint                        | Description         |
| ------ | ------------------------------- | ------------------- |
| GET    | `/api/bases/`                   | List all bases      |
| POST   | `/api/bases/`                   | Create base         |
| GET    | `/api/bases/<id>/`              | Get base details    |
| PATCH  | `/api/bases/<id>/`              | Update base         |
| DELETE | `/api/bases/<id>/`              | Delete base         |
| GET    | `/api/bases/<id>/drones/`       | Get drones at base  |
| GET    | `/api/bases/<id>/stats/`        | Get base statistics |
| GET    | `/api/bases/nearest/?lat=&lng=` | Find nearest base   |

### Fleet (Drones)

| Method | Endpoint                  | Description       |
| ------ | ------------------------- | ----------------- |
| GET    | `/api/fleet/drones/`      | List all drones   |
| POST   | `/api/fleet/drones/`      | Register drone    |
| GET    | `/api/fleet/drones/<id>/` | Get drone details |
| PATCH  | `/api/fleet/drones/<id>/` | Update drone      |
| DELETE | `/api/fleet/drones/<id>/` | Delete drone      |
| GET    | `/api/fleet/stats/`       | Fleet statistics  |

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

### Analytics

| Method | Endpoint                             | Description                 |
| ------ | ------------------------------------ | --------------------------- |
| GET    | `/api/analytics/overview/`           | System-wide analytics       |
| GET    | `/api/analytics/missions/timeline/`  | Mission completion timeline |
| GET    | `/api/analytics/drones/utilization/` | Drone utilization metrics   |

### WebSocket

Real-time telemetry updates:

```
ws://localhost:8000/ws/missions/<mission_id>/telemetry/
```

## 🎨 Frontend Routes

| Route              | Component      | Description                    |
| ------------------ | -------------- | ------------------------------ |
| `/bases`           | Bases          | Base management (default page) |
| `/drones`          | Drone          | Drone fleet dashboard          |
| `/missions`        | Missions       | Mission list and history       |
| `/mission/planner` | MissionPlanner | Create new missions            |
| `/mission/monitor` | LiveMonitor    | Real-time mission tracking     |
| `/analytics`       | Analytics      | Statistics and charts          |

## 📦 Project Structure

### Frontend Components

```
static/app/
├── components/
│   ├── common/
│   │   ├── Layout.tsx              # Main app layout with sidebar
│   │   └── DeviceRestriction.tsx   # Desktop-only restriction
│   └── ui/                          # shadcn/ui components
│       ├── badge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       └── table.tsx
├── pages/
│   ├── Bases.tsx                    # Base CRUD with map
│   ├── Drone.tsx                    # Drone fleet with hero layout
│   ├── Missions.tsx                 # Mission management
│   ├── MissionPlanner.tsx           # Mission creation wizard
│   ├── LiveMonitor.tsx              # WebSocket telemetry
│   └── Analytics.tsx                # Charts and metrics
├── services/
│   ├── baseService.ts               # Base API client
│   ├── droneService.ts              # Drone API client
│   └── missionService.ts            # Mission API client
└── types/
    ├── base.ts                      # Base interfaces
    ├── drone.ts                     # Drone interfaces
    └── mission.ts                   # Mission interfaces
```

### Backend Services

```
src/dsms/services/
├── fleet_service.py          # Drone CRUD operations
├── mission_service.py        # Mission lifecycle management
├── path_generator.py         # Flight path algorithms
├── analytics_service.py      # Statistics computation
└── telemetry_service.py      # Real-time data streaming
```

## 🚀 Deployment

### Docker Deployment (Recommended)

Build and deploy using the provided Dockerfile:

```bash
# Build Docker image
docker build -t dsms:latest .

# Run container
docker run -p 8000:8000 \
  -e MONGODB_URI=your_mongodb_uri \
  -e REDIS_URL=your_redis_url \
  -e SECRET_KEY=your_secret_key \
  dsms:latest
```

The Docker build process:

1. Installs Python and Node.js dependencies
2. Builds the React frontend with Webpack
3. Collects Django static files
4. Serves both frontend and API from port 8000

### Manual Deployment

**1. Build Frontend:**

```bash
npm ci --production=false
npm run build
```

**2. Collect Static Files:**

```bash
python manage.py collectstatic --noinput
```

**3. Set Production Environment:**

```bash
export DJANGO_SETTINGS_MODULE=dsms.conf.settings.production
export SECRET_KEY=your-production-secret-key
```

**4. Run with Gunicorn:**

```bash
gunicorn dsms.wsgi:application --bind 0.0.0.0:8000
```

### Environment Variables for Production

```bash
# Required
MONGODB_URI=mongodb+srv://...
REDIS_URL=redis://...
SECRET_KEY=production-secret-key
DJANGO_SETTINGS_MODULE=dsms.conf.settings.production

# Optional
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## 🎯 Key Features Explained

### Base Management

- Create operational bases with geographic coordinates
- View all bases on an interactive Leaflet map
- Status tracking (active, maintenance, offline)
- Filter bases by status
- Edit base details and status inline
- View drone count per base

### Drone Fleet

- Support for 12 DJI drone models with authentic specifications
- Hero layout with large drone images
- Real-time battery and status monitoring
- Add new drones with detailed specifications
- Assign drones to specific bases
- Filter by base and status
- Delete drones with confirmation

### Mission Planning

- Draw coverage areas on map
- Multiple flight patterns: crosshatch, perimeter, spiral, waypoint
- Configurable altitude, speed, and overlap
- Automatic waypoint generation
- Assign drones from available fleet
- Schedule mission start times

### Real-time Monitoring

- WebSocket-based telemetry streaming
- Live drone position updates on map
- Battery level tracking
- Mission progress percentage
- Pause/resume/abort controls

### Analytics

- Fleet utilization metrics
- Mission completion statistics
- Drone health monitoring
- Historical performance data

## 🛠️ Technology Highlights

- **React Query**: Efficient data fetching with automatic caching and background updates
- **shadcn/ui**: Accessible, customizable components built on Radix UI
- **Tailwind CSS**: Utility-first styling with neutral color scheme
- **TypeScript**: Full type safety across the frontend
- **Leaflet**: Interactive maps with custom markers and polygons
- **MongoEngine**: Elegant MongoDB ODM for Python
- **Django Channels**: WebSocket support for real-time features
- **Celery**: Background task processing for mission execution

## 📖 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) - System design and patterns
- [API Reference](docs/API.md) - Complete API documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production setup instructions
- [Setup Guide](docs/SETUP.md) - Detailed development setup

## 🐛 Troubleshooting

### Frontend build errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### MongoDB connection issues

- Verify MONGODB_URI in .env
- Check IP whitelist in MongoDB Atlas
- Ensure database user has proper permissions

### WebSocket not connecting

- Check Redis is running
- Verify REDIS_URL in .env
- Ensure CORS settings allow WebSocket connections

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built for the FlytBase Design Challenge** 🚁
