# System Architecture

Technical architecture and design documentation for the Drone Survey Management System.

## Architecture Overview

DSMS follows a modern full-stack architecture with clear separation between frontend, backend, and data layers.

```
┌─────────────────────────────────────────────────────────┐
│                    Client Browser                        │
│                  (React + TypeScript)                    │
└────────────┬────────────────────────────────────────────┘
             │ HTTP/REST + WebSocket
             │
┌────────────▼────────────────────────────────────────────┐
│                   Django Backend                         │
│  ┌──────────────┬────────────────┬──────────────────┐  │
│  │  REST API    │   WebSocket    │  Background      │  │
│  │  (DRF)       │   (Channels)   │  Tasks (Celery)  │  │
│  └──────┬───────┴────────┬───────┴────────┬─────────┘  │
│         │                 │                 │            │
│  ┌──────▼─────────────────▼─────────────────▼────────┐  │
│  │           Service Layer (Business Logic)          │  │
│  └──────┬────────────────────────────────────────────┘  │
│         │                                                │
│  ┌──────▼────────────────────────────────────────────┐  │
│  │      Model Layer (MongoEngine ODM)                │  │
│  └──────┬────────────────────────────────────────────┘  │
└─────────┼────────────────────────────────────────────────┘
          │
┌─────────▼─────────────┐      ┌──────────────────┐
│   MongoDB Atlas       │      │      Redis       │
│   (Database)          │      │  (Channel Layer) │
└───────────────────────┘      └──────────────────┘
```

## Technology Stack

### Frontend Layer

**React 18.3** - UI Framework

- Component-based architecture
- Hooks for state management
- TypeScript for type safety

**TanStack Query** - Data Management

- Server state caching
- Automatic refetching
- Optimistic updates
- Polling for real-time updates (1s intervals)

**Leaflet** - Mapping

- Interactive map rendering
- Polygon drawing and visualization
- Marker positioning for drones
- Multi-layer support (coverage, paths)

**Tailwind CSS** - Styling

- Utility-first CSS framework
- Custom theme configuration
- Responsive design

**Webpack** - Build Tool

- Module bundling
- Development server with HMR
- Production optimization

### Backend Layer

**Django 6.0** - Web Framework

- URL routing
- Middleware pipeline
- Settings management
- Development server

**Django REST Framework** - API Layer

- Serialization/deserialization
- ViewSets and routers
- Authentication/permissions
- API browsing interface

**Django Channels** - WebSocket Support

- ASGI protocol support
- WebSocket consumers
- Channel layers for broadcasting
- Group messaging

**MongoEngine** - ODM (Object-Document Mapper)

- Schema definition
- Query abstraction
- Relationship management
- Validation

### Data Layer

**MongoDB Atlas** - Primary Database

- Document-oriented NoSQL
- Flexible schema
- High availability
- Cloud-hosted

**Redis** - Cache & Channel Layer

- WebSocket message broker
- Session storage
- Real-time pub/sub

## System Components

### 1. API Layer (`src/dsms/api/`)

#### Endpoints (`api/endpoints/`)

- `drone_index.py` - Drone CRUD operations
- `drone_details.py` - Individual drone details
- `mission_index.py` - Mission listing and creation
- `mission_details.py` - Mission management
- `mission_control.py` - Start/pause/resume/abort
- `fleet_stats.py` - Fleet statistics
- `analytics.py` - Mission analytics

#### Serializers (`api/serializers/`)

- `drone.py` - Drone data serialization
- `mission.py` - Mission data serialization
- `telemetry.py` - Telemetry data serialization

### 2. Service Layer (`src/dsms/services/`)

**Business logic separation from views**

- `fleet_service.py`
    - Drone status management
    - Fleet statistics calculation
    - Stale status cleanup
- `mission_service.py`
    - Mission CRUD operations
    - Area calculation (Shoelace formula)
    - Flight path generation
    - Mission lifecycle management
- `telemetry_service.py`
    - Telemetry recording
    - Position updates
    - Historical data retrieval
- `path_generator.py`
    - Crosshatch pattern generation
    - Waypoint calculation
    - Distance estimation
- `analytics_service.py`
    - Mission statistics
    - Performance metrics

### 3. Model Layer (`src/dsms/models/`)

**MongoDB Document Schemas**

#### Drone Model

```python
{
    drone_id: String (unique)
    name: String
    model: String
    status: Enum [available, in_flight, charging, maintenance, offline]
    battery_level: Float
    location: GeoJSON Point
    current_mission_id: String
    home_location: GeoJSON Point
    last_seen: DateTime
}
```

#### Mission Model

```python
{
    mission_id: String (unique)
    name: String
    site_name: String
    coverage_area: GeoJSON Polygon
    flight_path: {
        waypoints: [Waypoint]
        total_distance: Float
        estimated_duration: Float
        pattern_type: Enum
    }
    status: Enum [draft, scheduled, in_progress, paused, completed, aborted, failed]
    progress: Float
    assigned_drone_id: String
    area_covered: Float
    images_captured: Int
}
```

#### Telemetry Model

```python
{
    mission_id: String
    drone_id: String
    position: GeoJSON Point
    altitude: Float
    battery: Float
    speed: Float
    heading: Float
}
```

### 4. Background Tasks (`src/dsms/tasks/`)

#### Simulator (`simulator.py`)

- `run_mission_simulation_sync()` - Main simulation loop
- Physics-based movement calculation
- Waypoint navigation
- Battery consumption simulation
- Auto-recovery on server restart
- Database retry logic

#### Celery Tasks (`celery.py`)

- Async task configuration
- Redis broker setup
- Task scheduling

### 5. WebSocket Layer (`src/dsms/consumers/`)

#### TelemetryConsumer

- WebSocket connection handling
- Real-time telemetry broadcasting
- Group-based messaging
- Connection state management

**URL Pattern**: `ws://localhost:8000/ws/missions/<mission_id>/telemetry/`

### 6. Frontend Architecture (`static/app/`)

#### Pages

- `Dashboard.tsx` - Fleet overview and statistics
- `MissionPlanner.tsx` - Mission creation with map
- `LiveMonitor.tsx` - Real-time mission tracking
- `Analytics.tsx` - Mission reports and visualization

#### Services

- `api.ts` - Axios client configuration
- `droneService.ts` - Drone API calls
- `missionService.ts` - Mission API calls

#### Types

- `drone.ts` - Drone TypeScript interfaces
- `mission.ts` - Mission TypeScript interfaces
- `telemetry.ts` - Telemetry TypeScript interfaces

## Data Flow

### Mission Creation Flow

```
User → MissionPlanner → API → MissionService → MongoDB
  1. Draw polygon on map
  2. Fill form data
  3. Submit → POST /api/missions/
  4. create_mission() validates and saves
  5. Returns mission with generated ID
```

### Mission Start Flow

```
User → LiveMonitor → API → MissionService → Simulator
  1. Click Start → POST /api/missions/{id}/start/
  2. start_mission() updates status
  3. Assigns drone (marks as in_flight)
  4. Spawns simulator thread
  5. Simulator runs in background
  6. Broadcasts telemetry via Channels
```

### Real-time Updates Flow

```
Simulator → MongoDB → API → Frontend (Polling)
  1. Simulator updates drone position
  2. Records telemetry to database
  3. Frontend polls every 1 second
  4. GET /api/missions/{id}/telemetry/?limit=1
  5. Updates map marker position
```

### Area Calculation Flow

```
Mission Completion → Service Layer → MongoDB
  1. complete_mission() triggered
  2. Extracts coverage_area.coordinates
  3. Applies Shoelace formula
  4. Converts degrees to meters
  5. Calculates polygon area
  6. Stores area_covered field
```

## Design Patterns

### Service Layer Pattern

- Business logic isolated from views
- Reusable across endpoints
- Easier testing and maintenance

### Repository Pattern

- MongoEngine provides data access abstraction
- Models define schema and validation
- Services use models for queries

### Observer Pattern (Planned)

- WebSocket consumers observe mission events
- Broadcast updates to subscribed clients
- Currently using polling as fallback

### Background Processing

- Celery for async tasks
- Threading for simulation
- Auto-recovery mechanism

## Security Considerations

### API Security

- CORS headers configured
- CSRF protection (Django default)
- Input validation via serializers
- Query parameter sanitization

### Database Security

- MongoDB Atlas with authentication
- Connection string in environment variables
- Network whitelist in Atlas

### Frontend Security

- TypeScript type checking
- Input sanitization
- XSS protection via React

## Performance Optimizations

### Frontend

- TanStack Query caching
- Lazy loading components (potential)
- Webpack code splitting
- Tailwind CSS purging

### Backend

- MongoDB connection pooling (10-50 connections)
- Redis caching for channel layer
- Database retry logic (3 attempts)
- Efficient queries with MongoEngine

### Simulator

- Threaded execution (non-blocking)
- Batch telemetry recording
- Graceful degradation on DB errors

## Scalability Considerations

### Horizontal Scaling

- Stateless API design
- Session storage in Redis
- MongoDB replica sets

### Vertical Scaling

- Async operations via Celery
- Connection pooling
- Background task processing

### Future Improvements

- Kubernetes deployment
- Load balancing
- CDN for static assets
- WebSocket for all real-time updates
- Database sharding

## Monitoring & Logging

### Current Implementation

- Python logging to console
- Django debug toolbar (dev)
- Browser console for frontend
- MongoDB Atlas monitoring

### Recommended Additions

- Sentry for error tracking
- Prometheus + Grafana for metrics
- ELK stack for log aggregation
- APM for performance monitoring

## Development Workflow

### Local Development

1. Code changes trigger Webpack HMR
2. Python changes require server restart
3. Database migrations not needed (NoSQL)
4. Redis optional for development

### Testing Strategy

- Unit tests with Pytest (backend)
- Component tests with Jest (frontend)
- Integration tests for API endpoints
- E2E tests with Selenium (future)

### CI/CD Pipeline (Recommended)

1. Code push to GitHub
2. Run linters (Black, ESLint)
3. Run tests (Pytest, Jest)
4. Build Docker images
5. Deploy to staging
6. Manual approval for production

## Technology Decisions

### Why MongoDB?

- Flexible schema for evolving drone data
- GeoJSON support for spatial queries
- Horizontal scaling capabilities
- Easy replication and sharding

### Why Django Channels?

- WebSocket support in Django ecosystem
- Built on ASGI standard
- Redis channel layer for broadcasting
- Seamless integration with Django

### Why React + TypeScript?

- Component reusability
- Type safety prevents bugs
- Large ecosystem and community
- Modern development experience

### Why TanStack Query?

- Automatic caching and refetching
- Optimistic updates
- Loading/error states
- Polling support for real-time

## References

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Channels](https://channels.readthedocs.io/)
- [MongoEngine](http://mongoengine.org/)
- [React Documentation](https://react.dev/)
- [TanStack Query](https://tanstack.com/query/)
- [Leaflet](https://leafletjs.com/)
