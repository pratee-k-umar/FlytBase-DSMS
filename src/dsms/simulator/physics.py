"""
Physics calculations for drone simulation.
"""
import math
from typing import Tuple

from dsms.utils.geo import haversine_distance, interpolate_position


def calculate_movement(
    current: Tuple[float, float],
    target: Tuple[float, float],
    speed: float,
    delta: float
) -> Tuple[Tuple[float, float], float, bool]:
    """
    Calculate drone movement toward a target.
    
    Args:
        current: Current (lng, lat)
        target: Target (lng, lat)
        speed: Speed in m/s
        delta: Time delta in seconds
    
    Returns:
        Tuple of (new_position, distance_moved, reached_target)
    """
    distance_to_target = haversine_distance(
        current[0], current[1],
        target[0], target[1]
    )
    
    max_distance = speed * delta
    
    if distance_to_target <= max_distance:
        # Reached target
        return (target, distance_to_target, True)
    else:
        # Move toward target
        fraction = max_distance / distance_to_target
        new_pos = interpolate_position(current, target, fraction)
        return (new_pos, max_distance, False)


def drain_battery(current_level: float, delta_seconds: float) -> float:
    """
    Calculate battery drain.
    
    Assumes roughly 0.5% per minute drain rate.
    
    Args:
        current_level: Current battery percentage
        delta_seconds: Time elapsed in seconds
    
    Returns:
        New battery level
    """
    drain_rate = 0.5 / 60  # % per second
    new_level = current_level - (drain_rate * delta_seconds)
    return max(0.0, new_level)


def calculate_eta(
    distance_remaining: float,
    speed: float
) -> int:
    """
    Calculate estimated time of arrival.
    
    Args:
        distance_remaining: Distance in meters
        speed: Speed in m/s
    
    Returns:
        ETA in seconds
    """
    if speed <= 0:
        return 0
    return int(distance_remaining / speed)


def interpolate_altitude(
    current_alt: float,
    target_alt: float,
    fraction: float
) -> float:
    """
    Interpolate altitude during flight.
    
    Args:
        current_alt: Current altitude in meters
        target_alt: Target altitude in meters
        fraction: Progress fraction (0.0 to 1.0)
    
    Returns:
        Interpolated altitude
    """
    return current_alt + (target_alt - current_alt) * fraction
