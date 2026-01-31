"""
Drone Model
Defines the schema for drone fleet management.
"""

from mongoengine import (
    StringField, FloatField, IntField, BooleanField,
    DictField, EmbeddedDocumentField, ListField
)
from dsms.models.base import BaseDocument


class Drone(BaseDocument):
    """
    Represents a drone in the fleet with its capabilities,
    status, and current operational state.
    """
    
    # Identity
    drone_id = StringField(required=True, unique=True)
    name = StringField(required=True)
    model = StringField(required=True)
    manufacturer = StringField()
    
    # Status
    status = StringField(
        required=True,
        choices=['available', 'in_flight', 'charging', 'maintenance', 'offline'],
        default='available'
    )
    battery_level = FloatField(min_value=0, max_value=100, default=100)
    
    # Location (current position)
    location = DictField(default=lambda: {'lat': 0.0, 'lng': 0.0, 'alt': 0.0})
    
    # Capabilities
    max_flight_time = IntField(default=30)  # minutes
    max_speed = FloatField(default=15.0)  # m/s
    max_altitude = FloatField(default=120.0)  # meters
    camera_specs = DictField()
    payload_capacity = FloatField(default=0.5)  # kg
    
    # Site Information
    home_base = DictField()  # {lat, lng, alt}
    assigned_site = StringField()
    
    # Health & Maintenance
    total_flight_hours = FloatField(default=0.0)
    last_maintenance = StringField()  # ISO datetime
    health_status = StringField(choices=['good', 'warning', 'critical'], default='good')
    
    # Assignment
    current_mission_id = StringField()
    
    meta = {
        'collection': 'drones',
        'indexes': [
            'drone_id',
            'status',
            'assigned_site',
            'current_mission_id',
        ]
    }
    
    def __str__(self):
        return f"Drone({self.drone_id}, {self.status})"
