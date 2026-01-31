"""
Telemetry Model
Defines time-series data for drone telemetry during missions.
"""

from datetime import datetime, timedelta
from mongoengine import (
    StringField, FloatField, IntField,
    DictField, DateTimeField
)
from dsms.models.base import BaseDocument


class TelemetryPoint(BaseDocument):
    """
    Time-series telemetry data point from a drone during mission execution.
    Includes position, battery, speed, and other flight metrics.
    """
    
    # References
    mission_id = StringField(required=True, db_field='missionId')
    drone_id = StringField(required=True, db_field='droneId')
    
    # Timestamp
    timestamp = DateTimeField(default=datetime.utcnow, required=True)
    
    # Position
    position = DictField(required=True)  # {lat, lng, alt}
    
    # Flight State
    battery = FloatField(required=True, min_value=0, max_value=100)
    speed = FloatField(default=0.0)  # m/s
    heading = FloatField(default=0.0)  # degrees
    altitude_agl = FloatField(default=0.0)  # meters above ground level
    
    # Progress
    waypoint_index = IntField(default=0)
    progress = FloatField(default=0.0)  # percentage
    
    # Status
    status = StringField(
        choices=['flying', 'hovering', 'landing', 'error'],
        default='flying'
    )
    
    # Sensors (optional)
    sensors = DictField()  # Additional sensor data
    
    # Alerts
    alerts = DictField()  # Any warnings or alerts
    
    meta = {
        'collection': 'telemetry',
        'indexes': [
            'mission_id',
            'drone_id',
            '-timestamp',  # Descending for latest-first queries
            {
                'fields': ['timestamp'],
                'expireAfterSeconds': 2592000  # 30 days TTL
            }
        ]
    }
    
    def __str__(self):
        return f"Telemetry({self.drone_id}, {self.timestamp})"
