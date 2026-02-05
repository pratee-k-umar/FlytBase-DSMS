# API Reference

Complete REST API documentation for the Drone Survey Management System.

## Base URL

```
http://localhost:8000/api
```

## Response Format

All API responses follow this structure:

### Success Response

```json
{
  "data": <response data>,
  "count": <number of items> (for list endpoints)
}
```

### Error Response

```json
{
    "error": "Error message",
    "detail": "Detailed error information"
}
```

## Authentication

Currently no authentication is required. Add authentication headers when implemented:

```http
Authorization: Bearer <token>
```

---

## Base Management

### List All Bases

Get list of all operational bases.

**Endpoint**: `GET /api/bases/`

**Query Parameters**: None

**Response**:

```json
{
    "data": [
        {
            "base_id": "BASE-0001",
            "name": "Central Operations",
            "lat": 12.9716,
            "lng": 77.5946,
            "status": "active",
            "capacity": 50,
            "drone_count": 35,
            "created_at": "2026-01-15T10:00:00Z",
            "updated_at": "2026-02-05T08:30:00Z"
        }
    ],
    "count": 5
}
```

**Status Codes**:

- `200 OK` - Success

---

### Create Base

Create a new operational base.

**Endpoint**: `POST /api/bases/`

**Request Body**:

```json
{
    "name": "North Operations",
    "lat": 13.0827,
    "lng": 80.2707,
    "capacity": 40,
    "status": "active"
}
```

**Response**:

```json
{
    "base_id": "BASE-0006",
    "name": "North Operations",
    "lat": 13.0827,
    "lng": 80.2707,
    "capacity": 40,
    "status": "active",
    "drone_count": 0,
    "created_at": "2026-02-05T10:00:00Z"
}
```

**Status Codes**:

- `201 Created` - Base created successfully
- `400 Bad Request` - Invalid input data

---

### Get Base Details

Get detailed information about a specific base.

**Endpoint**: `GET /api/bases/{base_id}/`

**Parameters**:

- `base_id` (path) - Base identifier (e.g., "BASE-0001")

**Response**:

```json
{
    "base_id": "BASE-0001",
    "name": "Central Operations",
    "lat": 12.9716,
    "lng": 77.5946,
    "status": "active",
    "capacity": 50,
    "drone_count": 35,
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-02-05T08:30:00Z"
}
```

**Status Codes**:

- `200 OK` - Success
- `404 Not Found` - Base not found

---

### Update Base

Update base information.

**Endpoint**: `PATCH /api/bases/{base_id}/`

**Request Body** (partial update):

```json
{
    "status": "maintenance",
    "capacity": 60
}
```

**Response**:

```json
{
    "base_id": "BASE-0001",
    "name": "Central Operations",
    "status": "maintenance",
    "capacity": 60,
    "updated_at": "2026-02-05T12:00:00Z"
}
```

**Status Codes**:

- `200 OK` - Updated successfully
- `404 Not Found` - Base not found

---

### Delete Base

Delete an operational base.

**Endpoint**: `DELETE /api/bases/{base_id}/`

**Response**: `204 No Content`

**Status Codes**:

- `204 No Content` - Deleted successfully
- `404 Not Found` - Base not found

---

### Get Base Drones

Get all drones assigned to a specific base.

**Endpoint**: `GET /api/bases/{base_id}/drones/`

**Response**:

```json
{
    "data": [
        {
            "drone_id": "DRN-0001",
            "name": "Alpha-001",
            "model": "DJI Mavic 4 Pro",
            "status": "available",
            "battery_level": 100
        }
    ],
    "count": 35
}
```

---

### Get Base Statistics

Get operational statistics for a base.

**Endpoint**: `GET /api/bases/{base_id}/stats/`

**Response**:

```json
{
    "total_drones": 35,
    "available": 28,
    "in_mission": 5,
    "maintenance": 2,
    "utilization": 71.4
}
```

---

### Find Nearest Base

Find the nearest base to given coordinates.

**Endpoint**: `GET /api/bases/nearest/`

**Query Parameters**:

- `lat` (float, required) - Latitude
- `lng` (float, required) - Longitude

**Response**:

```json
{
    "base_id": "BASE-0002",
    "name": "East Hub",
    "distance": 12.5,
    "lat": 12.935,
    "lng": 77.6244
}
```

---

## Fleet Management

### List All Drones

Get list of all drones in the fleet.

**Endpoint**: `GET /api/fleet/drones/`

**Query Parameters**: None

**Response**:

```json
{
    "data": [
        {
            "id": "507f1f77bcf86cd799439011",
            "drone_id": "DRN-0001",
            "name": "Alpha-001",
            "model": "DJI Mavic 4 Pro",
            "manufacturer": "DJI",
            "image_url": "/static/drone-gallery/dji-mavic-4-pro.png",
            "status": "available",
            "battery_level": 95.5,
            "location": {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "altitude": 0
            },
            "base_id": "BASE-0001",
            "current_mission_id": null,
            "max_flight_time": 45,
            "max_speed": 21.0,
            "max_altitude": 120.0,
            "payload_capacity": 1.2,
            "health_status": "good",
            "total_flight_hours": 125.5,
            "created_at": "2026-01-20T08:00:00Z"
        }
    ],
    "count": 240
}
```

**Status Codes**:

- `200 OK` - Success

---

### Register New Drone

Add a new drone to the fleet.

**Endpoint**: `POST /api/fleet/drones/`

**Request Body**:

```json
{
    "name": "Beta-050",
    "model": "DJI Air 3S",
    "manufacturer": "DJI",
    "base_id": "BASE-0002",
    "max_flight_time": 40,
    "max_speed": 19.0,
    "max_altitude": 120.0,
    "payload_capacity": 0.8
}
```

**Response**:

```json
{
    "drone_id": "DRN-0241",
    "name": "Beta-050",
    "model": "DJI Air 3S",
    "status": "available",
    "battery_level": 100,
    "created_at": "2026-02-05T14:00:00Z"
}
```

**Status Codes**:

- `201 Created` - Drone registered successfully
- `400 Bad Request` - Invalid input data

---

### Get Drone Details

Get detailed information about a specific drone.

**Endpoint**: `GET /api/fleet/drones/{drone_id}/`

**Parameters**:

- `drone_id` (path) - Drone identifier (e.g., "DRN-0001")

**Response**:

```json
{
    "id": "507f1f77bcf86cd799439011",
    "drone_id": "DRN-0001",
    "name": "Surveyor Alpha",
    "model": "DJI Phantom 4 Pro",
    "status": "in_flight",
    "battery_level": 87.3,
    "location": {
        "type": "Point",
        "coordinates": [77.5946, 12.9716]
    },
    "current_mission_id": "MSN-0005",
    "home_location": {
        "type": "Point",
        "coordinates": [77.59, 12.97]
    },
    "max_flight_time": 30,
    "max_speed": 15.0,
    "last_maintenance": "2026-01-15T10:00:00Z",
    "last_seen": "2026-01-31T12:30:00Z"
}
```

**Status Codes**:

- `200 OK` - Success
- `404 Not Found` - Drone not found

---

### Get Fleet Statistics

Get aggregated fleet statistics.

**Endpoint**: `GET /api/fleet/stats/`

**Query Parameters**: None

**Response**:

```json
{
    "data": {
        "total": 4,
        "available": 2,
        "in_mission": 1,
        "charging": 0,
        "maintenance": 1,
        "offline": 0,
        "average_battery": 92.5,
        "low_battery": 0
    }
}
```

**Status Codes**:

- `200 OK` - Success

---

## Mission Management

### List Missions

Get list of missions with optional filtering.

**Endpoint**: `GET /api/missions/`

**Query Parameters**:

- `status` (optional) - Filter by status: `draft`, `scheduled`, `in_progress`, `paused`, `completed`, `aborted`, `failed`
- `site` (optional) - Filter by site name
- `drone_id` (optional) - Filter by assigned drone

**Example**:

```
GET /api/missions/?status=in_progress
```

**Response**:

```json
{
    "data": [
        {
            "id": "507f1f77bcf86cd799439012",
            "mission_id": "MSN-0001",
            "name": "Campus Survey",
            "site_name": "Tech Campus",
            "status": "in_progress",
            "progress": 45.5,
            "assigned_drone_id": "DRN-0001",
            "coverage_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [77.59, 12.97],
                        [77.6, 12.97],
                        [77.6, 12.98],
                        [77.59, 12.98],
                        [77.59, 12.97]
                    ]
                ]
            },
            "altitude": 50.0,
            "speed": 10.0,
            "overlap": 70.0,
            "survey_type": "mapping",
            "created_at": "2026-01-31T10:00:00Z",
            "started_at": "2026-01-31T10:15:00Z",
            "estimated_duration": 25
        }
    ],
    "count": 1
}
```

**Status Codes**:

- `200 OK` - Success

---

### Get Mission Details

Get detailed information about a specific mission.

**Endpoint**: `GET /api/missions/{mission_id}/`

**Parameters**:

- `mission_id` (path) - Mission identifier (e.g., "MSN-0001")

**Response**:

```json
{
    "id": "507f1f77bcf86cd799439012",
    "mission_id": "MSN-0001",
    "name": "Campus Survey",
    "description": "Aerial survey of campus buildings",
    "site_name": "Tech Campus",
    "status": "in_progress",
    "progress": 45.5,
    "current_waypoint_index": 23,
    "assigned_drone_id": "DRN-0001",
    "coverage_area": {
        "type": "Polygon",
        "coordinates": [
            [
                [77.59, 12.97],
                [77.6, 12.97],
                [77.6, 12.98],
                [77.59, 12.98],
                [77.59, 12.97]
            ]
        ]
    },
    "flight_path": {
        "waypoints": [
            { "lat": 12.97, "lng": 77.59, "alt": 50.0, "action": "fly" },
            { "lat": 12.971, "lng": 77.59, "alt": 50.0, "action": "photo" }
        ],
        "total_distance": 5420.5,
        "estimated_duration": 542,
        "pattern_type": "crosshatch"
    },
    "altitude": 50.0,
    "speed": 10.0,
    "overlap": 70.0,
    "survey_type": "mapping",
    "area_covered": 125000.5,
    "images_captured": 42,
    "created_at": "2026-01-31T10:00:00Z",
    "started_at": "2026-01-31T10:15:00Z",
    "completed_at": null
}
```

**Status Codes**:

- `200 OK` - Success
- `404 Not Found` - Mission not found

---

### Create Mission

Create a new mission.

**Endpoint**: `POST /api/missions/`

**Request Body**:

```json
{
    "name": "Campus Survey",
    "description": "Aerial survey of campus buildings",
    "site_name": "Tech Campus",
    "coverage_area": {
        "type": "Polygon",
        "coordinates": [
            [
                [77.59, 12.97],
                [77.6, 12.97],
                [77.6, 12.98],
                [77.59, 12.98],
                [77.59, 12.97]
            ]
        ]
    },
    "altitude": 50.0,
    "speed": 10.0,
    "overlap": 70.0,
    "survey_type": "mapping",
    "assigned_drone_id": "DRN-0001"
}
```

**Required Fields**:

- `name` - Mission name
- `site_name` - Site location name
- `coverage_area` - GeoJSON Polygon

**Optional Fields**:

- `description` - Mission description
- `altitude` - Flight altitude in meters (default: 50.0)
- `speed` - Flight speed in m/s (default: 10.0)
- `overlap` - Photo overlap percentage (default: 70.0)
- `survey_type` - Type: mapping, inspection, surveillance, delivery (default: mapping)
- `assigned_drone_id` - Drone to assign
- `scheduled_start` - ISO 8601 datetime

**Response**: Same as Get Mission Details

**Status Codes**:

- `201 Created` - Mission created successfully
- `400 Bad Request` - Invalid input data
- `404 Not Found` - Assigned drone not found

---

### Update Mission

Update an existing mission (only in draft status).

**Endpoint**: `PUT /api/missions/{mission_id}/`

**Request Body**: Same as Create Mission

**Response**: Updated mission details

**Status Codes**:

- `200 OK` - Mission updated
- `400 Bad Request` - Invalid data or mission not in draft
- `404 Not Found` - Mission not found

---

### Delete Mission

Delete a mission (only in draft status).

**Endpoint**: `DELETE /api/missions/{mission_id}/`

**Response**:

```json
{
    "message": "Mission deleted successfully"
}
```

**Status Codes**:

- `200 OK` - Mission deleted
- `400 Bad Request` - Mission not in draft status
- `404 Not Found` - Mission not found

---

### Start Mission

Start a mission and begin drone simulation.

**Endpoint**: `POST /api/missions/{mission_id}/start/`

**Request Body**: None required

**Response**: Updated mission with status "in_progress"

**Status Codes**:

- `200 OK` - Mission started
- `400 Bad Request` - Mission not in draft/scheduled or no drone assigned
- `404 Not Found` - Mission or drone not found

---

### Pause Mission

Pause an in-progress mission.

**Endpoint**: `POST /api/missions/{mission_id}/pause/`

**Response**: Updated mission with status "paused"

**Status Codes**:

- `200 OK` - Mission paused
- `400 Bad Request` - Mission not in progress

---

### Resume Mission

Resume a paused mission.

**Endpoint**: `POST /api/missions/{mission_id}/resume/`

**Response**: Updated mission with status "in_progress"

**Status Codes**:

- `200 OK` - Mission resumed
- `400 Bad Request` - Mission not paused

---

### Abort Mission

Abort a mission and return drone to available status.

**Endpoint**: `POST /api/missions/{mission_id}/abort/`

**Response**: Updated mission with status "aborted"

**Status Codes**:

- `200 OK` - Mission aborted
- `400 Bad Request` - Mission not in progress/paused

---

## Telemetry

### Get Mission Telemetry

Get telemetry data for a mission.

**Endpoint**: `GET /api/missions/{mission_id}/telemetry/`

**Query Parameters**:

- `limit` (optional) - Number of records to return (default: 100, max: 10000)

**Example**:

```
GET /api/missions/MSN-0001/telemetry/?limit=1
```

**Response**:

```json
{
    "data": [
        {
            "id": "507f1f77bcf86cd799439013",
            "mission_id": "MSN-0001",
            "drone_id": "DRN-0001",
            "timestamp": "2026-01-31T12:30:45Z",
            "position": {
                "type": "Point",
                "coordinates": [77.595, 12.972]
            },
            "altitude": 50.2,
            "battery": 87.3,
            "speed": 10.1,
            "heading": 45.0
        }
    ],
    "count": 1
}
```

**Status Codes**:

- `200 OK` - Success
- `404 Not Found` - Mission not found

---

## Analytics

### Get Mission Statistics

Get aggregated mission statistics.

**Endpoint**: `GET /api/missions/stats/`

**Response**:

```json
{
    "total": 15,
    "draft": 2,
    "scheduled": 1,
    "in_progress": 2,
    "paused": 0,
    "completed": 8,
    "aborted": 1,
    "failed": 1
}
```

**Status Codes**:

- `200 OK` - Success

---

## WebSocket API

### Telemetry Stream

Real-time telemetry updates via WebSocket.

**URL**: `ws://localhost:8000/ws/missions/{mission_id}/telemetry/`

**Connection**:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/missions/MSN-0001/telemetry/");

ws.onopen = () => {
    console.log("Connected to telemetry stream");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Telemetry update:", data);
};
```

**Message Types**:

**Connection Established**:

```json
{
    "type": "connection_established",
    "mission_id": "MSN-0001",
    "message": "Connected to telemetry stream"
}
```

**Telemetry Update**:

```json
{
    "type": "telemetry_update",
    "data": {
        "position": { "type": "Point", "coordinates": [77.595, 12.972] },
        "altitude": 50.2,
        "battery": 87.3,
        "speed": 10.1,
        "heading": 45.0,
        "timestamp": "2026-01-31T12:30:45Z"
    }
}
```

**Status Update**:

```json
{
    "type": "status_update",
    "data": {
        "status": "completed",
        "progress": 100.0,
        "message": "Mission completed successfully"
    }
}
```

---

## Error Codes

| Code | Description                             |
| ---- | --------------------------------------- |
| 200  | OK - Request successful                 |
| 201  | Created - Resource created successfully |
| 400  | Bad Request - Invalid input data        |
| 404  | Not Found - Resource not found          |
| 500  | Internal Server Error - Server error    |

---

## Rate Limiting

Currently no rate limiting is implemented. Recommended limits for production:

- 100 requests per minute per IP for general endpoints
- 1000 requests per minute for telemetry endpoints

---

## Examples

### Python (requests)

```python
import requests

# Get all drones
response = requests.get('http://localhost:8000/api/fleet/drones/')
drones = response.json()['data']

# Create mission
mission_data = {
    'name': 'Test Survey',
    'site_name': 'Test Site',
    'coverage_area': {
        'type': 'Polygon',
        'coordinates': [[[77.59, 12.97], [77.60, 12.97], [77.60, 12.98], [77.59, 12.98], [77.59, 12.97]]]
    },
    'assigned_drone_id': 'DRN-0001'
}
response = requests.post('http://localhost:8000/api/missions/', json=mission_data)
mission = response.json()

# Start mission
requests.post(f'http://localhost:8000/api/missions/{mission["mission_id"]}/start/')
```

### JavaScript (fetch)

```javascript
// Get fleet stats
const response = await fetch("http://localhost:8000/api/fleet/stats/");
const stats = await response.json();
console.log(stats.data);

// Get mission telemetry
const telemetryResponse = await fetch(
    "http://localhost:8000/api/missions/MSN-0001/telemetry/?limit=10",
);
const telemetry = await telemetryResponse.json();
```

### cURL

```bash
# List missions
curl http://localhost:8000/api/missions/

# Get specific mission
curl http://localhost:8000/api/missions/MSN-0001/

# Create mission
curl -X POST http://localhost:8000/api/missions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Survey",
    "site_name": "Test Site",
    "coverage_area": {
      "type": "Polygon",
      "coordinates": [[[77.59, 12.97], [77.60, 12.97], [77.60, 12.98], [77.59, 12.98], [77.59, 12.97]]]
    }
  }'

# Start mission
curl -X POST http://localhost:8000/api/missions/MSN-0001/start/
```

---

## Changelog

### Version 1.0 (Current)

- Initial API release
- Fleet management endpoints
- Mission CRUD operations
- Mission control (start/pause/resume/abort)
- Telemetry retrieval
- WebSocket telemetry streaming
- Analytics endpoints
