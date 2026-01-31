"""
Path Generator Service
Algorithms for generating flight paths.
"""

import math
from typing import Any, Dict, List

from dsms.models.mission import FlightPath, Waypoint


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
    This creates parallel lines across the survey area, clipped to polygon boundaries.
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
    # Approximate: 1 degree ≈ 111km at equator
    # For a camera with ~50m swath at 50m altitude, adjust accordingly
    swath_width = altitude * 0.8  # Approximate ground coverage in meters
    spacing_meters = swath_width * (1 - overlap / 100)
    spacing_degrees = spacing_meters / 111000  # Convert to degrees

    waypoints = []
    current_lat = min_lat
    direction = 1  # 1 = left to right, -1 = right to left

    while current_lat <= max_lat:
        # Generate points along this latitude line
        line_points = []
        num_points = 20  # Sample points along the line

        for i in range(num_points + 1):
            lng = min_lng + (max_lng - min_lng) * i / num_points
            if point_in_polygon(lng, current_lat, coords):
                line_points.append((lng, current_lat))

        # Group consecutive points into segments
        if line_points:
            segments = []
            current_segment = [line_points[0]]

            for i in range(1, len(line_points)):
                # If points are close together, they're part of same segment
                if (
                    abs(line_points[i][0] - line_points[i - 1][0])
                    < (max_lng - min_lng) / num_points * 1.5
                ):
                    current_segment.append(line_points[i])
                else:
                    if len(current_segment) > 1:
                        segments.append(current_segment)
                    current_segment = [line_points[i]]

            if len(current_segment) > 1:
                segments.append(current_segment)

            # Add waypoints for each segment
            for segment in segments:
                if direction == 1:
                    # Left to right
                    for point in segment:
                        waypoints.append(
                            Waypoint(
                                lng=point[0],
                                lat=point[1],
                                alt=altitude,
                                action="photo",
                            )
                        )
                else:
                    # Right to left
                    for point in reversed(segment):
                        waypoints.append(
                            Waypoint(
                                lng=point[0],
                                lat=point[1],
                                alt=altitude,
                                action="photo",
                            )
                        )

        current_lat += spacing_degrees
        direction *= -1  # Alternate direction

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
