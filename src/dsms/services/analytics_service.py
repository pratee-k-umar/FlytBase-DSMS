"""
Analytics Service
Business logic for analytics and statistics.
"""
from datetime import datetime, timedelta
from typing import Dict, Any

from dsms.db import connect_db

# Ensure DB connection
connect_db()

from dsms.models import Mission, Drone, TelemetryPoint


def get_summary() -> Dict[str, Any]:
    """Get organization-wide analytics summary"""
    
    # Mission statistics
    total_missions = Mission.objects.count()
    missions_by_status = {
        'draft': Mission.objects.filter(status='draft').count(),
        'scheduled': Mission.objects.filter(status='scheduled').count(),
        'in_progress': Mission.objects.filter(status='in_progress').count(),
        'paused': Mission.objects.filter(status='paused').count(),
        'completed': Mission.objects.filter(status='completed').count(),
        'aborted': Mission.objects.filter(status='aborted').count(),
        'failed': Mission.objects.filter(status='failed').count(),
    }
    
    # Completed missions stats
    completed_missions = list(Mission.objects.filter(status='completed'))
    
    total_flight_time = 0
    total_distance = 0
    
    for mission in completed_missions:
        if mission.started_at and mission.completed_at:
            duration = (mission.completed_at - mission.started_at).total_seconds()
            total_flight_time += duration
        
        if mission.flight_path and mission.flight_path.total_distance:
            total_distance += mission.flight_path.total_distance
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_missions = Mission.objects.filter(created_at__gte=week_ago).count()
    recent_completed = Mission.objects.filter(
        status='completed',
        completed_at__gte=week_ago
    ).count()
    
    # Drone statistics
    total_drones = Drone.objects.count()
    active_drones = Drone.objects.filter(status='in_flight').count()
    
    return {
        'missions': {
            'total': total_missions,
            'by_status': missions_by_status,
            'completed_count': len(completed_missions),
            'success_rate': round(
                len(completed_missions) / total_missions * 100, 1
            ) if total_missions > 0 else 0,
        },
        'operations': {
            'total_flight_time_seconds': int(total_flight_time),
            'total_flight_time_hours': round(total_flight_time / 3600, 2),
            'total_distance_meters': round(total_distance, 2),
            'total_distance_km': round(total_distance / 1000, 2),
        },
        'fleet': {
            'total_drones': total_drones,
            'active_drones': active_drones,
        },
        'recent_activity': {
            'missions_created_7d': recent_missions,
            'missions_completed_7d': recent_completed,
        },
    }


def get_mission_stats(mission_id: str) -> Dict[str, Any]:
    """Get statistics for a specific mission"""
    from dsms.services import mission_service
    
    mission = mission_service.get_mission(mission_id)
    
    # Get telemetry data
    telemetry_points = list(
        TelemetryPoint.objects.filter(mission_id=mission_id).order_by('timestamp')
    )
    
    stats = {
        'mission_id': mission.mission_id,
        'status': mission.status,
        'progress': mission.progress,
    }
    
    if mission.started_at:
        stats['started_at'] = mission.started_at.isoformat()
    
    if mission.completed_at:
        stats['completed_at'] = mission.completed_at.isoformat()
        if mission.started_at:
            duration = (mission.completed_at - mission.started_at).total_seconds()
            stats['duration_seconds'] = int(duration)
    
    if mission.flight_path:
        stats['planned_distance'] = mission.flight_path.total_distance
        stats['planned_duration'] = mission.flight_path.estimated_duration
        stats['waypoint_count'] = len(mission.flight_path.waypoints)
    
    if telemetry_points:
        stats['telemetry_points'] = len(telemetry_points)
        last_point = telemetry_points[-1]
        stats['actual_distance'] = last_point.distance_traveled
        
        # Calculate average speed
        speeds = [p.speed for p in telemetry_points if p.speed]
        if speeds:
            stats['average_speed'] = round(sum(speeds) / len(speeds), 2)
    
    return stats
