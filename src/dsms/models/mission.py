"""
Mission Model
Defines the schema for survey missions and flight paths.
"""

from mongoengine import (
    StringField, FloatField, IntField, BooleanField,
    DictField, EmbeddedDocument, EmbeddedDocumentField,
    ListField, DateTimeField
)
from dsms.models.base import BaseDocument


class Waypoint(EmbeddedDocument):
    """A single waypoint in a flight path."""
    lat = FloatField(required=True)
    lng = FloatField(required=True)
    alt = FloatField(required=True)
    action = StringField(choices=['fly', 'hover', 'photo', 'video'], default='fly')
    duration = FloatField(default=0)  # seconds to stay at waypoint


class FlightPath(EmbeddedDocument):
    """Complete flight path with waypoints and metadata."""
    waypoints = ListField(EmbeddedDocumentField(Waypoint))
    total_distance = FloatField()  # meters
    estimated_duration = FloatField()  # minutes
    pattern_type = StringField(
        choices=['crosshatch', 'perimeter', 'spiral', 'waypoint'],
        default='crosshatch'
    )


class Mission(BaseDocument):
    """
    Represents a survey mission with flight path, schedule,
    and execution state.
    """
    
    # Identity
    mission_id = StringField(required=True, unique=True)
    name = StringField(required=True)
    description = StringField()
    
    # Survey Details
    site_name = StringField(required=True)
    survey_type = StringField(
        choices=['mapping', 'inspection', 'surveillance', 'delivery'],
        default='mapping'
    )
    
    # Coverage Area (GeoJSON Polygon or bounding box)
    coverage_area = DictField()  # {type: 'Polygon', coordinates: [...]}
    
    # Flight Path
    flight_path = EmbeddedDocumentField(FlightPath)
    altitude = FloatField(default=50.0)  # meters AGL
    speed = FloatField(default=10.0)  # m/s
    overlap = FloatField(default=70.0)  # percentage for mapping missions
    
    # Schedule
    scheduled_start = DateTimeField()
    scheduled_end = DateTimeField()
    
    # Assignment
    assigned_drone_id = StringField()
    pilot_id = StringField()
    
    # Status
    status = StringField(
        required=True,
        choices=['draft', 'scheduled', 'in_progress', 'paused', 'completed', 'aborted', 'failed'],
        default='draft'
    )
    
    # Execution State
    progress = FloatField(default=0.0)  # percentage
    current_waypoint_index = IntField(default=0)
    actual_start_time = DateTimeField()
    actual_end_time = DateTimeField()
    started_at = DateTimeField()
    completed_at = DateTimeField()
    
    # Results
    images_captured = IntField(default=0)
    area_covered = FloatField(default=0.0)  # square meters
    
    # Priority
    priority = StringField(choices=['low', 'medium', 'high', 'critical'], default='medium')
    
    # Weather & Conditions
    weather_conditions = DictField()
    
    # Approval
    approval_status = StringField(
        choices=['pending', 'approved', 'rejected'],
        default='pending'
    )
    approved_by = StringField()
    approval_notes = StringField()
    
    meta = {
        'collection': 'missions',
        'indexes': [
            'mission_id',
            'status',
            'assigned_drone_id',
            'scheduled_start',
            'site_name',
            'priority',
        ]
    }
    
    def __str__(self):
        return f"Mission({self.mission_id}, {self.status})"
