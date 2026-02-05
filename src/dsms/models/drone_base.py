"""
DroneBase Model
Defines the schema for drone bases/stations.
"""

from datetime import datetime
from math import atan2, cos, radians, sin, sqrt

from mongoengine import DateTimeField, DictField, FloatField, IntField, StringField

from dsms.models.base import BaseDocument


class DroneBase(BaseDocument):
    """
    Represents a drone base/station where drones are stationed,
    charged, and dispatched from.
    """

    # Identity
    base_id = StringField(required=True, unique=True)
    name = StringField(required=True)

    # Location (GeoJSON Point format)
    location = DictField(
        required=True,
        default=lambda: {"type": "Point", "coordinates": [0.0, 0.0]},
    )
    address = StringField()
    region = StringField()  # e.g., "North America", "Europe", "Asia"

    # Status
    status = StringField(choices=["active", "maintenance", "offline"], default="active")

    # Capacity
    max_drones = IntField(default=50, min_value=1, max_value=100)

    # Operational Range (in kilometers)
    operational_radius = FloatField(default=15.0, min_value=1.0)  # Default 15km range

    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "drone_bases",
        "indexes": [
            "base_id",
            "status",
            "region",
        ],
    }

    def __str__(self):
        return f"DroneBase({self.base_id}, {self.name})"

    @property
    def coordinates(self):
        """Get coordinates as [lng, lat]"""
        return self.location.get("coordinates", [0, 0])

    @property
    def lat(self):
        return self.coordinates[1] if len(self.coordinates) > 1 else 0

    @property
    def lng(self):
        return self.coordinates[0] if len(self.coordinates) > 0 else 0

    def calculate_distance(self, target_lat, target_lng):
        """
        Calculate distance from base to target location using Haversine formula.
        Returns distance in kilometers.
        """
        # Earth radius in km
        R = 6371.0

        lat1 = radians(self.lat)
        lon1 = radians(self.lng)
        lat2 = radians(target_lat)
        lon2 = radians(target_lng)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return distance

    def is_location_in_range(self, target_lat, target_lng):
        """
        Check if a target location is within this base's operational range.
        Returns True if within range, False otherwise.
        """
        distance = self.calculate_distance(target_lat, target_lng)
        return distance <= self.operational_radius
