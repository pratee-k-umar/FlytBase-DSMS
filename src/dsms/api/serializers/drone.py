"""
Drone Serializers
Serialization/deserialization for Drone-related data.
"""

from rest_framework import serializers


class DroneSerializer(serializers.Serializer):
    """Serializer for Drone model - read operations"""

    id = serializers.CharField(source="drone_id", read_only=True)
    drone_id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    model = serializers.CharField(allow_blank=True, required=False)
    manufacturer = serializers.CharField(allow_blank=True, required=False)
    status = serializers.CharField(read_only=True)
    battery_level = serializers.FloatField(read_only=True)
    location = serializers.DictField(read_only=True)
    max_flight_time = serializers.IntegerField()
    max_speed = serializers.FloatField()
    max_altitude = serializers.FloatField()
    camera_specs = serializers.DictField(required=False)
    payload_capacity = serializers.FloatField(required=False)
    assigned_site = serializers.CharField(allow_blank=True, required=False)
    total_flight_hours = serializers.FloatField(read_only=True)
    health_status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class DroneCreateSerializer(serializers.Serializer):
    """Serializer for registering a new drone"""

    name = serializers.CharField(max_length=100)
    model = serializers.CharField(max_length=50, required=False, allow_blank=True)
    manufacturer = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    assigned_site = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    max_flight_time = serializers.IntegerField(default=30)
    max_speed = serializers.FloatField(default=15.0)
    max_altitude = serializers.FloatField(default=120.0)
    camera_specs = serializers.DictField(required=False)
    payload_capacity = serializers.FloatField(required=False, default=0.5)
    location = serializers.DictField(required=False)


class DroneUpdateSerializer(serializers.Serializer):
    """Serializer for updating a drone"""

    name = serializers.CharField(max_length=100, required=False)
    model = serializers.CharField(max_length=50, required=False, allow_blank=True)
    manufacturer = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    assigned_site = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=["available", "in_flight", "charging", "maintenance", "offline"],
        required=False,
    )
    battery_level = serializers.IntegerField(required=False, min_value=0, max_value=100)
    max_flight_time = serializers.IntegerField(required=False)
    max_speed = serializers.FloatField(required=False)
    max_altitude = serializers.FloatField(required=False)
    sensors = serializers.ListField(child=serializers.CharField(), required=False)
    last_location = serializers.DictField(required=False)
