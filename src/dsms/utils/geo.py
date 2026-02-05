"""
Geo Utilities
Helper functions for geographic calculations.
"""
import math
from typing import Tuple, List, Dict


def haversine_distance(
    lng1: float, lat1: float,
    lng2: float, lat2: float
) -> float:
    """
    Calculate the great circle distance between two points in meters.
    
    Args:
        lng1, lat1: First point (longitude, latitude)
        lng2, lat2: Second point (longitude, latitude)
    
    Returns:
        Distance in meters
    """
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def bearing(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """
    Calculate the initial bearing between two points.
    
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lng = math.radians(lng2 - lng1)
    
    x = math.sin(delta_lng) * math.cos(lat2_rad)
    y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng))
    
    initial_bearing = math.atan2(x, y)
    
    # Convert to degrees and normalize to 0-360
    return (math.degrees(initial_bearing) + 360) % 360


def destination_point(
    lng: float, lat: float,
    distance: float, bearing_deg: float
) -> Tuple[float, float]:
    """
    Calculate destination point given start, distance, and bearing.
    
    Args:
        lng, lat: Starting point
        distance: Distance in meters
        bearing_deg: Bearing in degrees
    
    Returns:
        Tuple of (longitude, latitude)
    """
    R = 6371000  # Earth's radius in meters
    
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    bearing_rad = math.radians(bearing_deg)
    
    lat2 = math.asin(
        math.sin(lat_rad) * math.cos(distance / R) +
        math.cos(lat_rad) * math.sin(distance / R) * math.cos(bearing_rad)
    )
    
    lng2 = lng_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance / R) * math.cos(lat_rad),
        math.cos(distance / R) - math.sin(lat_rad) * math.sin(lat2)
    )
    
    return (math.degrees(lng2), math.degrees(lat2))


def normalize_longitude(lng: float) -> float:
    """
    Normalize longitude to -180 to 180 range.
    """
    while lng > 180:
        lng -= 360
    while lng < -180:
        lng += 360
    return lng


def shortest_longitude_diff(lng1: float, lng2: float) -> float:
    """
    Calculate the shortest difference between two longitudes,
    accounting for the 180° wrap-around.
    
    Returns a value between -180 and 180.
    """
    diff = lng2 - lng1
    # Normalize to -180 to 180
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    return diff


def interpolate_position(
    start: Tuple[float, float],
    end: Tuple[float, float],
    fraction: float
) -> Tuple[float, float]:
    """
    Linear interpolation between two points, handling longitude wrap-around.
    
    Args:
        start: (lng, lat) of start point
        end: (lng, lat) of end point
        fraction: 0.0 to 1.0 representing progress
    
    Returns:
        Interpolated (lng, lat)
    """
    # Use shortest path for longitude (handles antimeridian crossing)
    lng_diff = shortest_longitude_diff(start[0], end[0])
    lng = normalize_longitude(start[0] + lng_diff * fraction)
    
    # Latitude is straightforward
    lat = start[1] + (end[1] - start[1]) * fraction
    return (lng, lat)


def polygon_centroid(coordinates: List[List[float]]) -> Tuple[float, float]:
    """
    Calculate the centroid of a polygon.
    
    Args:
        coordinates: List of [lng, lat] coordinates
    
    Returns:
        (lng, lat) of centroid
    """
    if not coordinates:
        return (0, 0)
    
    lng_sum = sum(c[0] for c in coordinates)
    lat_sum = sum(c[1] for c in coordinates)
    n = len(coordinates)
    
    return (lng_sum / n, lat_sum / n)


def polygon_bounds(coordinates: List[List[float]]) -> Dict[str, float]:
    """
    Get the bounding box of a polygon.
    
    Returns:
        Dict with min_lng, max_lng, min_lat, max_lat
    """
    if not coordinates:
        return {'min_lng': 0, 'max_lng': 0, 'min_lat': 0, 'max_lat': 0}
    
    lngs = [c[0] for c in coordinates]
    lats = [c[1] for c in coordinates]
    
    return {
        'min_lng': min(lngs),
        'max_lng': max(lngs),
        'min_lat': min(lats),
        'max_lat': max(lats),
    }
