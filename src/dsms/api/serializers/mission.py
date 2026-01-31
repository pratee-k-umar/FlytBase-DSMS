"""
Mission Serializers
Serialization/deserialization for Mission-related data.
"""

from rest_framework import serializers


class WaypointSerializer(serializers.Serializer):
    """Serializer for waypoint data"""

    lat = serializers.FloatField()
    lng = serializers.FloatField()
    alt = serializers.FloatField()
    action = serializers.ChoiceField(
        choices=["fly", "hover", "photo", "video"], default="fly", required=False
    )
    duration = serializers.FloatField(default=0, required=False)


class FlightPathSerializer(serializers.Serializer):
    """Serializer for flight path data"""

    pattern_type = serializers.ChoiceField(
        choices=["waypoint", "crosshatch", "perimeter", "spiral"], required=False
    )
    waypoints = WaypointSerializer(many=True, required=False)
    total_distance = serializers.FloatField(read_only=True, required=False)
    estimated_duration = serializers.IntegerField(read_only=True, required=False)


class MissionSerializer(serializers.Serializer):
    """Serializer for Mission model - read operations"""

    mission_id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    assigned_drone_id = serializers.CharField(read_only=True, allow_null=True)
    site_name = serializers.CharField(allow_blank=True, required=False)
    coverage_area = serializers.DictField(required=False)
    flight_path = FlightPathSerializer(required=False)
    altitude = serializers.FloatField()
    speed = serializers.FloatField()
    overlap = serializers.FloatField()
    survey_type = serializers.CharField()
    scheduled_start = serializers.DateTimeField(required=False, allow_null=True)
    status = serializers.CharField(read_only=True)
    progress = serializers.FloatField(read_only=True)
    current_waypoint_index = serializers.IntegerField(read_only=True)
    area_covered = serializers.FloatField(read_only=True, required=False)
    images_captured = serializers.IntegerField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)


class MissionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new mission"""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )
    assigned_drone_id = serializers.CharField(required=False, allow_null=True)
    drone_id = serializers.CharField(
        required=False, allow_null=True
    )  # Alias for assigned_drone_id
    site_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    site = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )  # Alias for site_name
    coverage_area = serializers.DictField(required=False)  # GeoJSON Polygon
    survey_area = serializers.DictField(required=False)  # Alias for coverage_area
    survey_type = serializers.ChoiceField(
        choices=["mapping", "inspection", "surveillance", "delivery"], default="mapping"
    )
    altitude = serializers.FloatField(default=50.0)
    speed = serializers.FloatField(default=10.0)
    overlap = serializers.FloatField(default=70.0, min_value=0, max_value=90)
    overlap_percentage = serializers.FloatField(
        required=False, min_value=0, max_value=90
    )  # Alias
    scheduled_start = serializers.DateTimeField(required=False, allow_null=True)
    waypoints = WaypointSerializer(many=True, required=False)


class MissionUpdateSerializer(serializers.Serializer):
    """Serializer for updating a mission"""

    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )
    assigned_drone_id = serializers.CharField(required=False, allow_null=True)
    drone_id = serializers.CharField(required=False, allow_null=True)  # Alias
    site_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    site = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )  # Alias
    coverage_area = serializers.DictField(required=False)
    survey_area = serializers.DictField(required=False)  # Alias
    survey_type = serializers.ChoiceField(
        choices=["mapping", "inspection", "surveillance", "delivery"], required=False
    )
    altitude = serializers.FloatField(required=False)
    speed = serializers.FloatField(required=False)
    overlap = serializers.FloatField(required=False, min_value=0, max_value=90)
    overlap_percentage = serializers.FloatField(
        required=False, min_value=0, max_value=90
    )  # Alias
    scheduled_start = serializers.DateTimeField(required=False, allow_null=True)
