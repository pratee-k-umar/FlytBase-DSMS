"""
Drone Simulator Engine
Simulates drone flight along a mission path.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Tuple

from dsms.utils.geo import bearing, haversine_distance, interpolate_position


class DroneSimulator:
    """
    Simulates a drone flying a mission.

    Generates realistic telemetry including:
    - Position interpolation between waypoints
    - Battery drain over time
    - Speed and heading calculations
    """

    # Simulation constants
    BATTERY_DRAIN_RATE = 0.5  # % per minute
    DEFAULT_SPEED = 5.0  # m/s
    WAYPOINT_THRESHOLD = 2.0  # meters to consider "reached"

    def __init__(self, mission):
        """
        Initialize simulator with a mission.

        Args:
            mission: Mission document with flight_path
        """
        self.mission = mission
        self.mission_id = mission.mission_id

        # Get drone - handle both drone reference and assigned_drone_id
        if hasattr(mission, "drone") and mission.drone:
            self.drone_id = mission.drone.drone_id
            initial_battery = mission.drone.battery_level if mission.drone else 100
        elif mission.assigned_drone_id:
            self.drone_id = mission.assigned_drone_id
            # Try to get battery from drone
            try:
                from dsms.models import Drone

                drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
                initial_battery = drone.battery_level
            except:
                initial_battery = 100
        else:
            self.drone_id = "SIM-DRONE"
            initial_battery = 100

        # Get waypoints
        self.waypoints = []
        if mission.flight_path and mission.flight_path.waypoints:
            self.waypoints = list(mission.flight_path.waypoints)

        # Initialize state
        self.current_waypoint_idx = mission.current_waypoint_index or 0

        # Starting position
        if self.waypoints:
            first_wp = self.waypoints[
                min(self.current_waypoint_idx, len(self.waypoints) - 1)
            ]
            # Handle both formats: GeoJSON location or lat/lng fields
            if hasattr(first_wp, "location") and first_wp.location:
                self.position = list(first_wp.location["coordinates"])
                self.altitude = first_wp.altitude
            else:
                # lat, lng, alt format
                self.position = [first_wp.lng, first_wp.lat]
                self.altitude = first_wp.alt
        else:
            self.position = [0.0, 0.0]
            self.altitude = 50.0

        # Movement state
        self.speed = mission.speed or self.DEFAULT_SPEED
        self.heading = 0.0
        self.battery = initial_battery

        # Progress tracking
        self.total_distance = self._calculate_total_distance()

        # Restore distance_traveled from mission progress if resuming
        if mission.progress and mission.progress > 0:
            # Calculate distance based on saved progress percentage
            self.distance_traveled = (mission.progress / 100.0) * self.total_distance
        else:
            self.distance_traveled = 0.0

        self.start_time = datetime.utcnow()

    def _calculate_total_distance(self) -> float:
        """Calculate total path distance"""
        if len(self.waypoints) < 2:
            return 0.0

        total = 0.0
        for i in range(len(self.waypoints) - 1):
            wp1 = self.waypoints[i]
            wp2 = self.waypoints[i + 1]

            # Handle both formats
            if hasattr(wp1, "location") and wp1.location:
                coord1 = wp1.location["coordinates"]
                coord2 = wp2.location["coordinates"]
            else:
                coord1 = [wp1.lng, wp1.lat]
                coord2 = [wp2.lng, wp2.lat]

            total += haversine_distance(coord1[0], coord1[1], coord2[0], coord2[1])

        return total

    def tick(self, delta_seconds: float = 1.0) -> Dict[str, Any]:
        """
        Advance simulation by delta_seconds.

        Args:
            delta_seconds: Time step in seconds

        Returns:
            Dict with current telemetry data
        """
        # Check if already complete
        if self.current_waypoint_idx >= len(self.waypoints):
            return self._create_result(complete=True)

        # Get current target waypoint
        target_wp = self.waypoints[self.current_waypoint_idx]

        # Handle both formats
        if hasattr(target_wp, "location") and target_wp.location:
            target_pos = target_wp.location["coordinates"]
            target_altitude = target_wp.altitude
        else:
            target_pos = [target_wp.lng, target_wp.lat]
            target_altitude = target_wp.alt

        # Calculate distance to target
        distance_to_target = haversine_distance(
            self.position[0], self.position[1], target_pos[0], target_pos[1]
        )

        # Calculate how far we can move this tick
        max_distance = self.speed * delta_seconds

        if distance_to_target <= max_distance:
            # We reach the waypoint this tick
            self.position = list(target_pos)
            self.altitude = target_altitude
            self.distance_traveled += distance_to_target

            # Move to next waypoint
            self.current_waypoint_idx += 1

            # Check if complete
            if self.current_waypoint_idx >= len(self.waypoints):
                return self._create_result(complete=True)
        else:
            # Interpolate position toward target
            fraction = max_distance / distance_to_target
            new_pos = interpolate_position(
                (self.position[0], self.position[1]),
                (target_pos[0], target_pos[1]),
                fraction,
            )
            self.position = list(new_pos)

            # Interpolate altitude
            altitude_diff = target_altitude - self.altitude
            self.altitude += altitude_diff * fraction

            self.distance_traveled += max_distance

        # Update heading
        self.heading = bearing(
            self.position[0], self.position[1], target_pos[0], target_pos[1]
        )

        # Drain battery
        self.battery = max(
            0, self.battery - (self.BATTERY_DRAIN_RATE * delta_seconds / 60)
        )

        return self._create_result(complete=False)

    def _create_result(self, complete: bool) -> Dict[str, Any]:
        """Create telemetry result dict"""
        progress = 0.0
        if self.total_distance > 0:
            progress = min(100.0, (self.distance_traveled / self.total_distance) * 100)
        elif complete:
            progress = 100.0

        return {
            "complete": complete,
            "position": self.position,
            "altitude": round(self.altitude, 2),
            "heading": round(self.heading, 2),
            "speed": round(self.speed, 2),
            "battery": round(self.battery, 1),
            "current_waypoint": self.current_waypoint_idx,
            "total_waypoints": len(self.waypoints),
            "progress": round(progress, 2),
            "distance_traveled": round(self.distance_traveled, 2),
            "distance_remaining": round(
                max(0, self.total_distance - self.distance_traveled), 2
            ),
        }

    def get_state(self) -> Dict[str, Any]:
        """Get current simulator state"""
        return {
            "mission_id": self.mission_id,
            "drone_id": self.drone_id,
            "current_waypoint": self.current_waypoint_idx,
            "total_waypoints": len(self.waypoints),
            "position": self.position,
            "altitude": self.altitude,
            "battery": self.battery,
            "distance_traveled": self.distance_traveled,
            "total_distance": self.total_distance,
        }
