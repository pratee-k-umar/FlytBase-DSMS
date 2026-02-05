"""
Base Serializers
Serializers for DroneBase model.
"""

from rest_framework import serializers


class DroneBaseSerializer(serializers.Serializer):
    """Serializer for DroneBase model - read operations"""

    base_id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    location = serializers.DictField()
    address = serializers.CharField(allow_blank=True, required=False)
    region = serializers.CharField(allow_blank=True, required=False)
    status = serializers.ChoiceField(
        choices=["active", "maintenance", "offline"],
        default="active",
    )
    max_drones = serializers.IntegerField(default=50, min_value=1, max_value=100)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    # Computed fields
    drone_count = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    def get_drone_count(self, obj):
        """Get count of drones at this base"""
        from dsms.models import Drone
        return Drone.objects(base_id=obj.base_id).count()

    def get_lat(self, obj):
        coords = obj.location.get("coordinates", [0, 0])
        return coords[1] if len(coords) > 1 else 0

    def get_lng(self, obj):
        coords = obj.location.get("coordinates", [0, 0])
        return coords[0] if len(coords) > 0 else 0


class CreateBaseSerializer(serializers.Serializer):
    """Serializer for creating a new drone base"""

    name = serializers.CharField(max_length=200)
    location = serializers.DictField(required=True)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    region = serializers.CharField(max_length=100, required=False, allow_blank=True)
    max_drones = serializers.IntegerField(default=50, min_value=1, max_value=100)


class UpdateBaseSerializer(serializers.Serializer):
    """Serializer for updating a drone base"""

    name = serializers.CharField(max_length=200, required=False)
    location = serializers.DictField(required=False)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    region = serializers.CharField(max_length=100, required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=["active", "maintenance", "offline"],
        required=False,
    )
    max_drones = serializers.IntegerField(min_value=1, max_value=100, required=False)


class BaseStatsSerializer(serializers.Serializer):
    """Serializer for base statistics"""

    total_bases = serializers.IntegerField()
    active_bases = serializers.IntegerField()
    total_capacity = serializers.IntegerField()
    total_drones_assigned = serializers.IntegerField()
    utilization = serializers.FloatField()


class AddDroneToBaseSerializer(serializers.Serializer):
    """Serializer for adding a drone to a base"""

    drone_id = serializers.CharField()


class NearestBaseQuerySerializer(serializers.Serializer):
    """Serializer for nearest base query parameters"""

    lat = serializers.FloatField()
    lng = serializers.FloatField()
