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
    BATTERY_DRAIN_RATE = 2.0  # % per minute (faster drain for demo)
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
        self.current_waypoint = self.current_waypoint_idx  # Alias for external access

        # Track travel vs survey vs return waypoints
        # Travel waypoints are those added when mission starts (use action='fly')
        # Survey waypoints typically have action='photo' or other survey actions
        # Return waypoints have action='return' or 'land'
        self.travel_waypoint_count = self._count_travel_waypoints()
        self.return_waypoint_start = self._find_return_waypoint_start()

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

        # Progress tracking - separate travel, survey, and return distances
        self.total_distance = self._calculate_total_distance()
        self.travel_distance = self._calculate_travel_distance()
        self.return_distance = self._calculate_return_distance()
        self.survey_distance = self.total_distance - self.travel_distance - self.return_distance

        # Restore distance_traveled from mission progress if resuming
        if mission.progress and mission.progress > 0:
            # Progress is based on survey distance, so calculate survey_distance_traveled
            self.survey_distance_traveled = (mission.progress / 100.0) * self.survey_distance
            # Total distance traveled includes completed travel phase + partial survey
            self.distance_traveled = self.travel_distance + self.survey_distance_traveled
        else:
            self.distance_traveled = 0.0
            self.survey_distance_traveled = 0.0

        self.start_time = datetime.utcnow()

    def _count_travel_waypoints(self) -> int:
        """Count the number of travel waypoints at the start of the path"""
        count = 0
        for wp in self.waypoints:
            action = getattr(wp, 'action', 'fly')
            if action == 'fly':
                count += 1
            else:
                break  # First non-fly waypoint marks start of survey
        return count

    def _find_return_waypoint_start(self) -> int:
        """Find the index where return waypoints begin"""
        for i, wp in enumerate(self.waypoints):
            action = getattr(wp, 'action', '')
            if action in ('return', 'land'):
                return i
        # No return waypoints found
        return len(self.waypoints)

    def is_traveling(self) -> bool:
        """Check if drone is still in travel phase (before survey waypoints)"""
        return self.current_waypoint_idx < self.travel_waypoint_count

    def is_surveying(self) -> bool:
        """Check if drone is in survey phase (between travel and return)"""
        return (self.current_waypoint_idx >= self.travel_waypoint_count and 
                self.current_waypoint_idx < self.return_waypoint_start)

    def is_returning(self) -> bool:
        """Check if drone is returning to base"""
        return (self.current_waypoint_idx >= self.return_waypoint_start and 
                self.current_waypoint_idx < len(self.waypoints))

    def _calculate_total_distance(self) -> float:
        """Calculate total path distance (travel + survey)"""
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

    def _calculate_travel_distance(self) -> float:
        """Calculate distance of travel phase (before survey starts)"""
        if len(self.waypoints) < 2 or self.travel_waypoint_count < 1:
            return 0.0

        travel_dist = 0.0
        # Calculate distance between travel waypoints (indices 0 to travel_waypoint_count-1)
        for i in range(min(self.travel_waypoint_count, len(self.waypoints) - 1)):
            wp1 = self.waypoints[i]
            wp2 = self.waypoints[i + 1]

            # Handle both formats
            if hasattr(wp1, "location") and wp1.location:
                coord1 = wp1.location["coordinates"]
                coord2 = wp2.location["coordinates"]
            else:
                coord1 = [wp1.lng, wp1.lat]
                coord2 = [wp2.lng, wp2.lat]

            travel_dist += haversine_distance(coord1[0], coord1[1], coord2[0], coord2[1])

        return travel_dist

    def _calculate_return_distance(self) -> float:
        """Calculate distance of return phase (after survey ends)"""
        if self.return_waypoint_start >= len(self.waypoints):
            return 0.0

        return_dist = 0.0
        # Calculate distance between return waypoints
        for i in range(self.return_waypoint_start, len(self.waypoints) - 1):
            wp1 = self.waypoints[i]
            wp2 = self.waypoints[i + 1]

            # Handle both formats
            if hasattr(wp1, "location") and wp1.location:
                coord1 = wp1.location["coordinates"]
                coord2 = wp2.location["coordinates"]
            else:
                coord1 = [wp1.lng, wp1.lat]
                coord2 = [wp2.lng, wp2.lat]

            return_dist += haversine_distance(coord1[0], coord1[1], coord2[0], coord2[1])

        return return_dist

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
            
            # Track survey distance separately (only after travel phase)
            if self.is_surveying():
                self.survey_distance_traveled += distance_to_target

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
            
            # Track survey distance separately (only after travel phase)
            if self.is_surveying():
                self.survey_distance_traveled += max_distance

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
        # Calculate progress based on SURVEY distance only (excludes travel phase)
        progress = 0.0
        if self.survey_distance > 0:
            progress = min(100.0, (self.survey_distance_traveled / self.survey_distance) * 100)
        elif complete:
            progress = 100.0
        
        # Determine mission phase
        if self.is_traveling():
            mission_phase = "traveling"
        elif self.is_surveying():
            mission_phase = "surveying"
        elif self.is_returning():
            mission_phase = "returning"
        elif complete:
            mission_phase = "completed"
        else:
            mission_phase = "unknown"

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
            "mission_phase": mission_phase,
            "distance_traveled": round(self.distance_traveled, 2),
            "survey_distance_traveled": round(self.survey_distance_traveled, 2),
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
