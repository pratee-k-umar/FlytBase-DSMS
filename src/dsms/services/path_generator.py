"""
Path Generator Service
Algorithms for generating flight paths.
"""

import math
from typing import Any, Dict, List

from dsms.models.mission import FlightPath, Waypoint
from dsms.utils.geo import normalize_longitude, shortest_longitude_diff


def normalize_survey_area(survey_area: Dict) -> Dict:
    """
    Normalize all coordinates in a GeoJSON polygon to valid ranges.
    This fixes issues from Leaflet map wrapping where longitudes can be
    outside the -180 to 180 range (e.g., -282 instead of 77).

    Args:
        survey_area: GeoJSON Polygon with potentially invalid coordinates

    Returns:
        GeoJSON Polygon with normalized coordinates
    """
    if not survey_area or "coordinates" not in survey_area:
        return survey_area

    normalized = {"type": survey_area.get("type", "Polygon"), "coordinates": []}

    for ring in survey_area["coordinates"]:
        normalized_ring = []
        for coord in ring:
            if len(coord) >= 2:
                # coord is [lng, lat] in GeoJSON
                normalized_coord = [
                    normalize_longitude(coord[0]),  # Normalize longitude
                    coord[1],  # Latitude doesn't need normalization (-90 to 90)
                ]
                # Preserve any additional elements (e.g., altitude)
                if len(coord) > 2:
                    normalized_coord.extend(coord[2:])
                normalized_ring.append(normalized_coord)
            else:
                normalized_ring.append(coord)
        normalized["coordinates"].append(normalized_ring)

    return normalized


def generate_path(
    survey_area: Dict, pattern: str, altitude: float, overlap: int, speed: float
) -> FlightPath:
    """
    Generate a flight path for a given survey area and pattern.

    Args:
        survey_area: GeoJSON Polygon defining the survey area
        pattern: 'waypoint', 'crosshatch', 'perimeter', 'spiral'
        altitude: Flight altitude in meters
        overlap: Overlap percentage for coverage
        speed: Flight speed in m/s

    Returns:
        FlightPath with generated waypoints
    """
    # Normalize coordinates first to handle Leaflet map wrapping
    survey_area = normalize_survey_area(survey_area)

    if pattern == "perimeter":
        waypoints = generate_perimeter_path(survey_area, altitude)
    elif pattern == "crosshatch":
        waypoints = generate_crosshatch_path(survey_area, altitude, overlap)
    elif pattern == "spiral":
        waypoints = generate_spiral_path(survey_area, altitude)
    else:
        # Default: just use polygon vertices as waypoints
        waypoints = generate_waypoint_path(survey_area, altitude)

    # Calculate total distance
    total_distance = calculate_path_distance(waypoints)
    estimated_duration = int(total_distance / speed) if speed > 0 else 0

    return FlightPath(
        pattern_type=pattern,
        waypoints=waypoints,
        total_distance=total_distance,
        estimated_duration=estimated_duration,
    )


def generate_travel_path(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    altitude: float,
    action: str = "fly",  # Valid actions: 'fly', 'hover', 'photo', 'video'
) -> List[Waypoint]:
    """
    Generate waypoints for traveling from one point to another.
    Creates a simple direct path with takeoff, cruise, and approach waypoints.

    Args:
        start_lat, start_lng: Starting position (base location)
        end_lat, end_lng: Ending position (mission start)
        altitude: Cruise altitude in meters
        action: Waypoint action type (must be one of: 'fly', 'hover', 'photo', 'video')

    Returns:
        List of Waypoint objects for the travel path
    """
    waypoints = []

    # 1. Takeoff waypoint (at start, low altitude) - only for outbound flight
    if action == "fly":
        waypoints.append(
            Waypoint(
                lat=start_lat,
                lng=start_lng,
                alt=10.0,  # Low altitude for takeoff
                action=action,
            )
        )

    # 2. Climb to cruise altitude (or start return at cruise)
    waypoints.append(
        Waypoint(lat=start_lat, lng=start_lng, alt=altitude, action=action)
    )

    # 3. Calculate intermediate waypoints for long distances
    distance = haversine_distance(start_lat, start_lng, end_lat, end_lng)

    # Add intermediate points for distances > 500m (every ~200m)
    if distance > 500:
        num_points = min(int(distance / 200), 10)  # Max 10 intermediate points

        # Calculate the shortest longitude difference (handles antimeridian)
        lng_diff = shortest_longitude_diff(start_lng, end_lng)

        for i in range(1, num_points):
            ratio = i / (num_points + 1)
            mid_lat = start_lat + ratio * (end_lat - start_lat)
            # Use shortest path for longitude to avoid going around the world
            mid_lng = normalize_longitude(start_lng + ratio * lng_diff)
            waypoints.append(
                Waypoint(lat=mid_lat, lng=mid_lng, alt=altitude, action=action)
            )

    # 4. Arrival point (at destination, cruise altitude)
    waypoints.append(Waypoint(lat=end_lat, lng=end_lng, alt=altitude, action=action))

    # 5. For return flights, add landing waypoint (descend to low altitude)
    if action == "fly":  # Changed from 'return' to 'fly'
        pass  # No additional landing waypoint needed
    # Landing handled by hover at final position

    return waypoints


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two lat/lng points"""
    R = 6371000  # Earth radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def generate_waypoint_path(survey_area: Dict, altitude: float) -> List[Waypoint]:
    """Generate waypoints from polygon vertices"""
    if not survey_area or "coordinates" not in survey_area:
        return []

    # GeoJSON Polygon: coordinates[0] is the outer ring
    coords = survey_area["coordinates"][0]
    waypoints = []

    for i, coord in enumerate(coords[:-1]):  # Skip last (duplicate of first)
        waypoint = Waypoint(
            lng=coord[0],
            lat=coord[1],
            alt=altitude,
            action="photo" if i > 0 else "fly",
        )
        waypoints.append(waypoint)

    return waypoints


def generate_perimeter_path(survey_area: Dict, altitude: float) -> List[Waypoint]:
    """Generate a perimeter path around the survey area"""
    if not survey_area or "coordinates" not in survey_area:
        return []

    coords = survey_area["coordinates"][0]
    waypoints = []

    for i, coord in enumerate(coords):
        waypoint = Waypoint(
            lng=coord[0],
            lat=coord[1],
            alt=altitude,
            action="photo",
        )
        waypoints.append(waypoint)

    return waypoints


def point_in_polygon(lng: float, lat: float, polygon_coords: List) -> bool:
    """Check if a point is inside a polygon using ray casting algorithm"""
    inside = False
    j = len(polygon_coords) - 1

    for i in range(len(polygon_coords)):
        xi, yi = polygon_coords[i][0], polygon_coords[i][1]
        xj, yj = polygon_coords[j][0], polygon_coords[j][1]

        if ((yi > lat) != (yj > lat)) and (
            lng < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i

    return inside


def generate_crosshatch_path(
    survey_area: Dict, altitude: float, overlap: int = 70
) -> List[Waypoint]:
    """
    Generate a crosshatch (lawn mower) pattern for full coverage.
    Creates clean parallel lines with only start/end points per line.
    """
    if not survey_area or "coordinates" not in survey_area:
        return []

    coords = survey_area["coordinates"][0]

    # Find bounding box
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    min_lng, max_lng = min(lngs), max(lngs)
    min_lat, max_lat = min(lats), max(lats)

    # Calculate line spacing based on overlap
    # For a camera with ~50m swath at 50m altitude
    swath_width = altitude * 0.8  # Approximate ground coverage in meters
    spacing_meters = swath_width * (1 - overlap / 100)
    # Minimum spacing to avoid too many lines
    spacing_meters = max(spacing_meters, 10)
    spacing_degrees = spacing_meters / 111000  # Convert to degrees

    waypoints = []
    current_lat = min_lat
    direction = 1  # 1 = left to right, -1 = right to left
    line_count = 0
    max_lines = 50  # Limit number of lines to prevent excessive waypoints

    while current_lat <= max_lat and line_count < max_lines:
        # Find intersection points with polygon at this latitude
        intersections = []

        for i in range(len(coords) - 1):
            x1, y1 = coords[i][0], coords[i][1]
            x2, y2 = coords[i + 1][0], coords[i + 1][1]

            # Check if this edge crosses our latitude line
            if (y1 <= current_lat <= y2) or (y2 <= current_lat <= y1):
                if y1 != y2:  # Avoid division by zero
                    # Calculate x intersection
                    x_intersect = x1 + (current_lat - y1) * (x2 - x1) / (y2 - y1)
                    intersections.append(x_intersect)

        # Sort intersections and pair them (entry/exit points)
        intersections.sort()

        # Create waypoints for each pair of intersections (inside polygon segments)
        for i in range(0, len(intersections) - 1, 2):
            start_lng = intersections[i]
            end_lng = (
                intersections[i + 1] if i + 1 < len(intersections) else intersections[i]
            )

            if direction == 1:
                # Left to right
                waypoints.append(
                    Waypoint(lng=start_lng, lat=current_lat, alt=altitude, action="fly")
                )
                waypoints.append(
                    Waypoint(lng=end_lng, lat=current_lat, alt=altitude, action="photo")
                )
            else:
                # Right to left
                waypoints.append(
                    Waypoint(lng=end_lng, lat=current_lat, alt=altitude, action="fly")
                )
                waypoints.append(
                    Waypoint(
                        lng=start_lng, lat=current_lat, alt=altitude, action="photo"
                    )
                )

        current_lat += spacing_degrees
        direction *= -1  # Alternate direction for lawn mower pattern
        line_count += 1

    return waypoints


def generate_spiral_path(survey_area: Dict, altitude: float) -> List[Waypoint]:
    """Generate a spiral path from outside to center"""
    if not survey_area or "coordinates" not in survey_area:
        return []

    coords = survey_area["coordinates"][0]

    # Find center and bounding box
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    center_lng = sum(lngs) / len(lngs)
    center_lat = sum(lats) / len(lats)

    # Calculate max radius
    max_radius = max(
        haversine_distance(center_lng, center_lat, c[0], c[1]) for c in coords
    )

    waypoints = []
    order = 0
    num_turns = 5  # Number of spiral turns
    points_per_turn = 12

    for i in range(num_turns * points_per_turn):
        # Spiral from outside to center
        t = 1 - (i / (num_turns * points_per_turn))
        radius = max_radius * t
        angle = i * (2 * math.pi / points_per_turn)

        # Convert to lat/lng offset (approximate)
        lng_offset = (
            radius * math.cos(angle) / 111000 / math.cos(math.radians(center_lat))
        )
        lat_offset = radius * math.sin(angle) / 111000

        waypoints.append(
            Waypoint(
                lng=center_lng + lng_offset,
                lat=center_lat + lat_offset,
                alt=altitude,
                action="photo",
            )
        )

    # End at center
    waypoints.append(
        Waypoint(
            lng=center_lng,
            lat=center_lat,
            alt=altitude,
            action="hover",
            duration=3,
        )
    )

    return waypoints


def calculate_path_distance(waypoints: List[Waypoint]) -> float:
    """Calculate total path distance in meters"""
    if len(waypoints) < 2:
        return 0.0

    total = 0.0
    for i in range(len(waypoints) - 1):
        wp1 = waypoints[i]
        wp2 = waypoints[i + 1]
        total += haversine_distance(wp1.lng, wp1.lat, wp2.lng, wp2.lat)

    return total


def haversine_distance(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Calculate distance between two coordinates in meters"""
    R = 6371000  # Earth's radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
