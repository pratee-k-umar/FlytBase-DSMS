"""
Telemetry Serializers
"""
from rest_framework import serializers


class TelemetrySerializer(serializers.Serializer):
    """Serializer for telemetry data"""
    mission_id = serializers.CharField()
    drone_id = serializers.CharField()
    timestamp = serializers.DateTimeField()
    location = serializers.DictField()
    altitude = serializers.FloatField()
    heading = serializers.FloatField()
    speed = serializers.FloatField()
    battery_level = serializers.IntegerField()
    signal_strength = serializers.IntegerField()
    current_waypoint_index = serializers.IntegerField()
    distance_traveled = serializers.FloatField()
    distance_remaining = serializers.FloatField()
    progress = serializers.FloatField()
