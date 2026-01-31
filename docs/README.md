# Drone Survey Management System (DSMS)

A comprehensive full-stack web application for managing drone survey operations, real-time mission monitoring, fleet management, and analytics.

## 🚁 Overview

DSMS provides a complete solution for drone-based survey operations with features including:

- **Mission Planning**: Draw survey areas on interactive maps and configure flight parameters
- **Live Monitoring**: Real-time drone tracking with telemetry updates
- **Fleet Management**: Monitor drone status, battery levels, and availability
- **Analytics**: Comprehensive mission reports with flight path visualization
- **Automated Simulation**: Background drone flight simulation with physics-based movement

## ✨ Key Features

### Mission Management

- Create missions with polygon survey areas
- Configure flight parameters (altitude, speed, overlap)
- Auto-generate crosshatch flight paths
- Assign drones to missions
- Track mission progress in real-time

### Live Monitoring

- Real-time drone position tracking on interactive maps
- Battery level and telemetry monitoring
- Coverage area visualization
- Mission control (pause, resume, abort)
- Auto-recovery for interrupted missions

### Fleet Dashboard

- Fleet status overview (total, available, in mission, maintenance)
- Individual drone status cards with battery indicators
- Real-time status updates

### Analytics & Reports

- Mission statistics (total, completed, in progress, failed)
- Fleet performance metrics
- Total flight time and area covered calculations
- Interactive mission details with flight path visualization
- Actual vs planned path comparison

## 🛠️ Tech Stack

### Backend

- Django 6.0.1 + Django REST Framework
- MongoDB with MongoEngine ODM
- Django Channels (WebSocket support)
- Redis (channel layer & caching)
- Celery (background tasks)

### Frontend

- React 18.3 + TypeScript 5.6
- TanStack Query (data fetching)
- Tailwind CSS (styling)
- Leaflet (interactive maps)
- Recharts (data visualization)

### Build & Dev Tools

- Webpack 5 (bundler)
- Babel 7 (transpiler)
- ESLint + Black (linters)
- Jest + Pytest (testing)

## 📁 Project Structure

```
FlytBase-DSMS/
├── src/dsms/              # Django backend
│   ├── api/               # REST API endpoints
│   ├── models/            # MongoDB models
│   ├── services/          # Business logic
│   ├── tasks/             # Background tasks & simulator
│   ├── consumers/         # WebSocket consumers
│   └── conf/              # Django configuration
├── static/app/            # React frontend
│   ├── pages/             # Page components
│   ├── services/          # API clients
│   ├── types/             # TypeScript types
│   └── components/        # Reusable components
├── docs/                  # Documentation
├── config/                # Configuration files
└── scripts/               # Utility scripts
```

## 🚀 Quick Start

See [SETUP.md](./SETUP.md) for detailed installation instructions.

```bash
# 1. Clone repository
git clone <repository-url>
cd FlytBase-DSMS

# 2. Install backend dependencies
cd src/dsms
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Install frontend dependencies
npm install

# 4. Configure environment
cp .env.example .env
# Edit .env with your MongoDB connection string

# 5. Run development server
python dev.py
```

Access the application at `http://localhost:8000`

## 📚 Documentation

- [Setup Guide](./SETUP.md) - Installation and configuration
- [Architecture](./ARCHITECTURE.md) - System design and components
- [API Reference](./API.md) - REST API endpoints
- [Deployment](./DEPLOYMENT.md) - Production deployment guide

## 🎯 Usage

### Creating a Mission

1. Navigate to **Mission Planner**
2. Fill in mission details (name, site, drone)
3. Draw survey area on the map
4. Configure flight parameters
5. Submit to create mission

### Monitoring Live Missions

1. Navigate to **Live Monitor**
2. Select an active mission from the list
3. View real-time drone position and telemetry
4. Control mission (pause/resume/abort)

### Viewing Analytics

1. Navigate to **Analytics**
2. View mission statistics and fleet performance
3. Click on completed missions to see detailed flight paths
4. Compare planned vs actual flight paths

## 🔧 Configuration

Key configuration in `.env`:

```env
MONGODB_URI=mongodb+srv://...
REDIS_URL=redis://localhost:6379/0
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
```

## 🧪 Testing

```bash
# Backend tests
cd src/dsms
pytest

# Frontend tests
npm test
```

## 📄 License

[Add your license here]

## 👥 Contributors

[Add contributors]

## 📞 Support

For issues and questions, please open a GitHub issue.
