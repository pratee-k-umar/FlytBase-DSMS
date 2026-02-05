"""
Base Service
Service functions for managing drone bases.
"""

import random
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from dsms.models import Drone, DroneBase
from dsms.utils.exceptions import NotFoundError, ValidationError


def get_country_code_from_api(lat: float, lng: float) -> str:
    """
    Get country code from BigDataCloud reverse geocoding API.
    Free API, no key required. Always returns English names.
    """
    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lng}&localityLanguage=en"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            country_code = data.get("countryCode", "XXX")
            return country_code if country_code else "XXX"
    except Exception as e:
        print(f"[WARNING] Geocoding API error: {e}")

    # Fallback to basic detection
    if 8.0 <= lat <= 37.0 and 68.0 <= lng <= 97.0:
        return "IND"
    elif 25.0 <= lat <= 49.0 and -125.0 <= lng <= -66.0:
        return "USA"
    return "XXX"


def get_location_details_from_api(lat: float, lng: float) -> Dict[str, str]:
    """
    Get address and region from BigDataCloud reverse geocoding API.
    Returns detailed location information in English for worldwide locations.
    """
    try:
        # localityLanguage=en ensures all responses are in English
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lng}&localityLanguage=en"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Extract address components (all in English)
            city = (
                data.get("city")
                or data.get("locality")
                or data.get("localityInfo", {})
                .get("administrative", [{}])[0]
                .get("name", "")
            )
            state = data.get("principalSubdivision", "")
            country = data.get("countryName", "")

            # Build address string
            address_parts = [p for p in [city, state] if p]
            address = (
                ", ".join(address_parts)
                if address_parts
                else f"Location: {lat:.4f}, {lng:.4f}"
            )

            # Use state or country as region
            region = state if state else country

            return {"address": address, "region": region or "Unknown"}
    except Exception as e:
        print(f"[WARNING] Geocoding API error: {e}")

    # Fallback to coordinates
    return {"address": f"Location: {lat:.4f}, {lng:.4f}", "region": "Unknown"}


def get_location_details(lat: float, lng: float) -> Dict[str, str]:
    """
    Get address and region from coordinates.
    This is a simplified reverse geocoding - in production you'd use a geocoding API.
    """
    # India regions
    if 8.0 <= lat <= 37.0 and 68.0 <= lng <= 97.0:
        # Mumbai area
        if 18.8 <= lat <= 19.3 and 72.7 <= lng <= 73.0:
            return {"address": "Mumbai Metropolitan Region", "region": "Maharashtra"}
        # Delhi area
        elif 28.4 <= lat <= 28.9 and 76.8 <= lng <= 77.5:
            return {"address": "National Capital Region", "region": "Delhi"}
        # Bangalore area
        elif 12.8 <= lat <= 13.2 and 77.4 <= lng <= 77.8:
            return {"address": "Bangalore Urban", "region": "Karnataka"}
        # Chennai area
        elif 12.9 <= lat <= 13.3 and 80.1 <= lng <= 80.4:
            return {"address": "Chennai Metropolitan Area", "region": "Tamil Nadu"}
        # Hyderabad area
        elif 17.2 <= lat <= 17.6 and 78.3 <= lng <= 78.7:
            return {"address": "Hyderabad Metropolitan Region", "region": "Telangana"}
        # Kolkata area
        elif 22.4 <= lat <= 22.7 and 88.2 <= lng <= 88.5:
            return {"address": "Kolkata Metropolitan Area", "region": "West Bengal"}
        # Pune area
        elif 18.4 <= lat <= 18.7 and 73.7 <= lng <= 74.0:
            return {"address": "Pune Metropolitan Region", "region": "Maharashtra"}
        # Ahmedabad area
        elif 22.9 <= lat <= 23.2 and 72.4 <= lng <= 72.8:
            return {"address": "Ahmedabad Urban Area", "region": "Gujarat"}
        # Jaipur area
        elif 26.7 <= lat <= 27.1 and 75.6 <= lng <= 76.0:
            return {"address": "Jaipur Metropolitan Area", "region": "Rajasthan"}
        # Kochi area
        elif 9.8 <= lat <= 10.1 and 76.1 <= lng <= 76.5:
            return {"address": "Kochi Metropolitan Region", "region": "Kerala"}
        # Generic India
        else:
            return {"address": f"Location: {lat:.4f}, {lng:.4f}", "region": "India"}

    # USA regions
    elif 25.0 <= lat <= 49.0 and -125.0 <= lng <= -66.0:
        # New York area
        if 40.5 <= lat <= 41.0 and -74.3 <= lng <= -73.7:
            return {"address": "New York Metropolitan Area", "region": "New York"}
        # Los Angeles area
        elif 33.7 <= lat <= 34.3 and -118.7 <= lng <= -118.1:
            return {"address": "Los Angeles County", "region": "California"}
        # Chicago area
        elif 41.6 <= lat <= 42.1 and -88.0 <= lng <= -87.5:
            return {"address": "Chicago Metropolitan Area", "region": "Illinois"}
        # Generic USA
        else:
            return {
                "address": f"Location: {lat:.4f}, {lng:.4f}",
                "region": "United States",
            }

    # Unknown location
    else:
        return {"address": f"Location: {lat:.4f}, {lng:.4f}", "region": "Unknown"}


def create_base(data: Dict[str, Any]) -> DroneBase:
    """Create a new drone base"""
    # Validate location
    if "location" not in data:
        raise ValidationError("Location is required")

    location = data["location"]
    if isinstance(location, dict) and "lat" in location and "lng" in location:
        lat = location["lat"]
        lng = location["lng"]
        # Convert simple lat/lng to GeoJSON
        location = {
            "type": "Point",
            "coordinates": [lng, lat],
        }
    else:
        # Extract from GeoJSON if already in that format
        lat = location["coordinates"][1]
        lng = location["coordinates"][0]

    # Get country code and location details from API (in English)
    country_code = get_country_code_from_api(lat, lng)
    location_details = get_location_details_from_api(lat, lng)

    # Use API data or user-provided data
    address = data.get("address", "") or location_details["address"]
    region = data.get("region", "") or location_details["region"]

    # Generate unique base_id with country code
    random_suffix = random.randint(100, 999)
    base_id = f"BASE-{country_code}-{random_suffix}"

    # Ensure uniqueness
    while DroneBase.objects.filter(base_id=base_id).first():
        random_suffix = random.randint(100, 999)
        base_id = f"BASE-{country_code}-{random_suffix}"

    base = DroneBase(
        base_id=base_id,
        name=data.get("name", f"Base {base_id}"),
        location=location,
        address=address,
        region=region,
        status=data.get("status", "active"),
        max_drones=data.get("max_drones", 50),
    )
    base.save()

    return base


def get_base(base_id: str) -> DroneBase:
    """Get a base by ID"""
    try:
        return DroneBase.objects.get(base_id=base_id)
    except DroneBase.DoesNotExist:
        raise NotFound(f"Base {base_id} not found")


def list_bases(filters: Optional[Dict] = None) -> List[DroneBase]:
    """List all bases with optional filters"""
    query = DroneBase.objects.all()

    if filters:
        if "status" in filters:
            query = query.filter(status=filters["status"])
        if "region" in filters:
            query = query.filter(region=filters["region"])

    return list(query.order_by("-created_at"))


def update_base(base_id: str, data: Dict[str, Any]) -> DroneBase:
    """Update a base"""
    base = get_base(base_id)

    if "name" in data:
        base.name = data["name"]
    if "address" in data:
        base.address = data["address"]
    if "region" in data:
        base.region = data["region"]
    if "status" in data:
        base.status = data["status"]
    if "max_drones" in data:
        base.max_drones = data["max_drones"]
    if "location" in data:
        location = data["location"]
        if isinstance(location, dict) and "lat" in location and "lng" in location:
            base.location = {
                "type": "Point",
                "coordinates": [location["lng"], location["lat"]],
            }
        else:
            base.location = location

    base.updated_at = datetime.utcnow()
    base.save()

    return base


def delete_base(base_id: str) -> bool:
    """Delete a base"""
    base = get_base(base_id)

    # Check if base has drones
    drone_count = Drone.objects(base_id=base_id).count()
    if drone_count > 0:
        raise ValidationError(
            f"Cannot delete base with {drone_count} drones. Reassign or remove drones first."
        )

    base.delete()
    return True


def get_drones_at_base(base_id: str) -> List[Drone]:
    """Get all drones assigned to a base"""
    get_base(base_id)  # Verify base exists
    return list(Drone.objects(base_id=base_id))


def get_drone_count(base_id: str) -> int:
    """Get count of drones at a base"""
    return Drone.objects(base_id=base_id).count()


def add_drone_to_base(base_id: str, drone_id: str) -> Drone:
    """Add/move a drone to a base"""
    base = get_base(base_id)

    # Check capacity
    current_count = get_drone_count(base_id)
    if current_count >= base.max_drones:
        raise ValidationError(
            f"Base {base_id} is at capacity ({base.max_drones} drones)"
        )

    try:
        drone = Drone.objects.get(drone_id=drone_id)
    except Drone.DoesNotExist:
        raise NotFound(f"Drone {drone_id} not found")

    drone.base_id = base_id
    # Update home_base location to match base
    drone.home_base = {"lat": base.lat, "lng": base.lng, "alt": 0}
    drone.save()

    return drone


def remove_drone_from_base(drone_id: str) -> Drone:
    """Remove a drone from its base"""
    try:
        drone = Drone.objects.get(drone_id=drone_id)
    except Drone.DoesNotExist:
        raise NotFound(f"Drone {drone_id} not found")

    drone.base_id = None
    drone.save()

    return drone


def find_nearest_base(lat: float, lng: float) -> Optional[DroneBase]:
    """Find the nearest active base to a given location"""
    # Use MongoDB geospatial query
    point = {"type": "Point", "coordinates": [lng, lat]}

    try:
        # Find nearest base using 2dsphere index
        nearest = DroneBase.objects(
            status="active",
            location__near=point,
        ).first()
        return nearest
    except Exception:
        # Fallback: manual distance calculation
        bases = DroneBase.objects(status="active")
        if not bases:
            return None

        from dsms.utils.geo import haversine_distance

        min_dist = float("inf")
        nearest_base = None

        for base in bases:
            base_coords = base.location.get("coordinates", [0, 0])
            dist = haversine_distance(lng, lat, base_coords[0], base_coords[1])
            if dist < min_dist:
                min_dist = dist
                nearest_base = base

        return nearest_base


def get_base_stats() -> Dict[str, Any]:
    """Get statistics for all bases"""
    total_bases = DroneBase.objects.count()
    active_bases = DroneBase.objects(status="active").count()
    total_capacity = sum(b.max_drones for b in DroneBase.objects.all())
    total_drones = Drone.objects(base_id__ne=None).count()

    return {
        "total_bases": total_bases,
        "active_bases": active_bases,
        "total_capacity": total_capacity,
        "total_drones_assigned": total_drones,
        "utilization": (
            round(total_drones / total_capacity * 100, 1) if total_capacity > 0 else 0
        ),
    }
