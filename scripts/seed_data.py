"""
Seed script to populate database with sample data.
Run from project root: python scripts/seed_data.py
"""

import os
import sys

# Add src directory to path so we can import dsms modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsms.conf.settings.development")

from dsms.db import connect_db

connect_db()

from dsms.models import Drone, FlightPath, Mission, Waypoint
from dsms.services import path_generator


def seed_drones():
    """Create sample drones"""
    print("Creating sample drones...")

    drones_data = [
        {
            "name": "Alpha Scout",
            "model": "DJI Mavic 3 Enterprise",
            "manufacturer": "DJI",
            "assigned_site": "San Francisco HQ",
            "location": {"lat": 37.7749, "lng": -122.4194, "alt": 0},
            "home_base": {"lat": 37.7749, "lng": -122.4194, "alt": 0},
        },
        {
            "name": "Beta Mapper",
            "model": "DJI Matrice 300 RTK",
            "manufacturer": "DJI",
            "assigned_site": "San Francisco HQ",
            "location": {"lat": 37.7755, "lng": -122.4180, "alt": 0},
            "home_base": {"lat": 37.7755, "lng": -122.4180, "alt": 0},
        },
        {
            "name": "Gamma Patrol",
            "model": "DJI Mavic 3",
            "manufacturer": "DJI",
            "assigned_site": "Los Angeles Depot",
            "location": {"lat": 34.0522, "lng": -118.2437, "alt": 0},
            "home_base": {"lat": 34.0522, "lng": -118.2437, "alt": 0},
        },
        {
            "name": "Delta Survey",
            "model": "Autel EVO II Pro",
            "manufacturer": "Autel",
            "assigned_site": "Los Angeles Depot",
            "location": {"lat": 34.0530, "lng": -118.2450, "alt": 0},
            "home_base": {"lat": 34.0530, "lng": -118.2450, "alt": 0},
        },
    ]

    for i, data in enumerate(drones_data):
        drone_id = f"DRN-{i + 1:04d}"

        # Check if drone already exists
        if Drone.objects.filter(drone_id=drone_id).first():
            print(f"Drone {drone_id} already exists, skipping")
            continue

        drone = Drone(
            drone_id=drone_id,
            name=data["name"],
            model=data["model"],
            manufacturer=data["manufacturer"],
            assigned_site=data["assigned_site"],
            location=data["location"],
            home_base=data["home_base"],
            status="available",
            battery_level=100,
            max_flight_time=30,
            max_speed=15.0,
            max_altitude=120.0,
        )
        drone.save()
        print(f"  [OK] Created {drone_id}: {data['name']}")

    print(f"  Total drones: {Drone.objects.count()}")


def seed_missions():
    """Create sample missions"""
    print("\nCreating sample missions...")

    # Get first available drone
    drone = Drone.objects.filter(status="available").first()

    if not drone:
        print("  [WARNING] No drones available, skipping missions")
        return

    missions_data = [
        {
            "name": "Warehouse Roof Inspection",
            "description": "Monthly inspection of warehouse rooftops for damage assessment",
            "site_name": "San Francisco HQ",
            "survey_type": "inspection",
            "coverage_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.4200, 37.7740],
                        [-122.4180, 37.7740],
                        [-122.4180, 37.7760],
                        [-122.4200, 37.7760],
                        [-122.4200, 37.7740],
                    ]
                ],
            },
            "pattern_type": "crosshatch",
            "altitude": 50.0,
            "speed": 5.0,
        },
        {
            "name": "Perimeter Security Patrol",
            "description": "Daily security patrol around facility perimeter",
            "site_name": "San Francisco HQ",
            "survey_type": "surveillance",
            "coverage_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.4210, 37.7735],
                        [-122.4170, 37.7735],
                        [-122.4170, 37.7765],
                        [-122.4210, 37.7765],
                        [-122.4210, 37.7735],
                    ]
                ],
            },
            "pattern_type": "perimeter",
            "altitude": 40.0,
            "speed": 8.0,
        },
        {
            "name": "Solar Panel Array Mapping",
            "description": "Thermal mapping of solar panel installations",
            "site_name": "Los Angeles Depot",
            "survey_type": "mapping",
            "coverage_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-118.2450, 34.0510],
                        [-118.2420, 34.0510],
                        [-118.2420, 34.0540],
                        [-118.2450, 34.0540],
                        [-118.2450, 34.0510],
                    ]
                ],
            },
            "pattern_type": "crosshatch",
            "altitude": 60.0,
            "speed": 4.0,
        },
    ]

    for i, data in enumerate(missions_data):
        mission_id = f"MSN-{i + 1:04d}"

        # Check if mission already exists
        if Mission.objects.filter(mission_id=mission_id).first():
            print(f"  Mission {mission_id} already exists, skipping")
            continue

        # Generate flight path
        flight_path = path_generator.generate_path(
            survey_area=data["coverage_area"],
            pattern=data["pattern_type"],
            altitude=data["altitude"],
            overlap=70,
            speed=data["speed"],
        )

        mission = Mission(
            mission_id=mission_id,
            name=data["name"],
            description=data["description"],
            site_name=data["site_name"],
            survey_type=data["survey_type"],
            coverage_area=data["coverage_area"],
            flight_path=flight_path,
            altitude=data["altitude"],
            speed=data["speed"],
            assigned_drone_id=drone.drone_id,
            status="draft",
        )
        mission.save()
        print(f"  [OK] Created {mission_id}: {data['name']}")
        print(
            f"     Pattern: {data['pattern_type']}, Waypoints: {len(flight_path.waypoints)}"
        )

    print(f"  Total missions: {Mission.objects.count()}")


def main():
    print("=" * 50)
    print("DSMS Database Seeder")
    print("=" * 50)

    seed_drones()
    seed_missions()

    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
