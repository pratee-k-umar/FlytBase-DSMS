"""
Seed script to populate database with sample data for India.
Creates 10 drone bases across India and 30-45 drones distributed among them.

Run from project root: python scripts/seed_india_data.py
"""

import os
import random
import sys
import uuid
from datetime import datetime, timedelta

# Add src directory to path so we can import dsms modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsms.conf.settings.development")

from dsms.db import connect_db

connect_db()

from dsms.models.drone import Drone
from dsms.models.drone_base import DroneBase

# Indian cities with coordinates (lat, lng)
INDIAN_BASES = [
    {
        "name": "Mumbai Coastal Base",
        "city": "Mumbai",
        "region": "Maharashtra",
        "lat": 19.0760,
        "lng": 72.8777,
        "address": "Bandra East, Mumbai, Maharashtra",
    },
    {
        "name": "Delhi NCR Hub",
        "city": "New Delhi",
        "region": "Delhi",
        "lat": 28.6139,
        "lng": 77.2090,
        "address": "Connaught Place, New Delhi",
    },
    {
        "name": "Bangalore Tech Park",
        "city": "Bangalore",
        "region": "Karnataka",
        "lat": 12.9716,
        "lng": 77.5946,
        "address": "Whitefield, Bangalore, Karnataka",
    },
    {
        "name": "Chennai Port Station",
        "city": "Chennai",
        "region": "Tamil Nadu",
        "lat": 13.0827,
        "lng": 80.2707,
        "address": "Anna Salai, Chennai, Tamil Nadu",
    },
    {
        "name": "Hyderabad Cyber Hub",
        "city": "Hyderabad",
        "region": "Telangana",
        "lat": 17.3850,
        "lng": 78.4867,
        "address": "HITEC City, Hyderabad, Telangana",
    },
    {
        "name": "Kolkata East Base",
        "city": "Kolkata",
        "region": "West Bengal",
        "lat": 22.5726,
        "lng": 88.3639,
        "address": "Salt Lake, Kolkata, West Bengal",
    },
    {
        "name": "Pune Smart City",
        "city": "Pune",
        "region": "Maharashtra",
        "lat": 18.5204,
        "lng": 73.8567,
        "address": "Hinjewadi, Pune, Maharashtra",
    },
    {
        "name": "Ahmedabad West Station",
        "city": "Ahmedabad",
        "region": "Gujarat",
        "lat": 23.0225,
        "lng": 72.5714,
        "address": "Satellite, Ahmedabad, Gujarat",
    },
    {
        "name": "Jaipur Heritage Base",
        "city": "Jaipur",
        "region": "Rajasthan",
        "lat": 26.9124,
        "lng": 75.7873,
        "address": "Vaishali Nagar, Jaipur, Rajasthan",
    },
    {
        "name": "Kochi Maritime Hub",
        "city": "Kochi",
        "region": "Kerala",
        "lat": 9.9312,
        "lng": 76.2673,
        "address": "Marine Drive, Kochi, Kerala",
    },
]

# Drone models and manufacturers
DRONE_MODELS = [
    {"model": "DJI Mavic 3 Enterprise", "manufacturer": "DJI"},
    {"model": "DJI Matrice 300 RTK", "manufacturer": "DJI"},
    {"model": "DJI Mavic 3", "manufacturer": "DJI"},
    {"model": "Parrot Anafi USA", "manufacturer": "Parrot"},
    {"model": "Autel EVO II Pro", "manufacturer": "Autel Robotics"},
    {"model": "Skydio X2", "manufacturer": "Skydio"},
    {"model": "DJI Phantom 4 RTK", "manufacturer": "DJI"},
    {"model": "Yuneec H520", "manufacturer": "Yuneec"},
]

# Drone name prefixes
DRONE_PREFIXES = [
    "Alpha",
    "Beta",
    "Gamma",
    "Delta",
    "Echo",
    "Falcon",
    "Guardian",
    "Hunter",
    "Sentinel",
    "Voyager",
    "Raptor",
    "Phoenix",
    "Eagle",
    "Hawk",
    "Thunder",
    "Lightning",
    "Storm",
    "Wind",
    "Sky",
    "Cloud",
    "Star",
    "Nova",
    "Comet",
]

# Drone statuses with weights for realistic distribution
DRONE_STATUSES = [
    ("available", 0.5),  # 50% available
    ("charging", 0.2),  # 20% charging
    ("maintenance", 0.1),  # 10% maintenance
    ("in_flight", 0.1),  # 10% in flight
    ("offline", 0.05),  # 5% offline
    ("returning", 0.05),  # 5% returning
]


def weighted_random_choice(choices):
    """Choose randomly based on weights."""
    items, weights = zip(*choices)
    return random.choices(items, weights=weights, k=1)[0]


def generate_drone_id():
    """Generate unique drone ID."""
    return f"DRN-{random.randint(1000, 9999)}-{random.randint(100, 999)}"


def clear_existing_data():
    """Clear existing drones and bases."""
    print("Clearing existing data...")
    Drone.objects.delete()
    DroneBase.objects.delete()
    print("✓ Existing data cleared")


def seed_bases():
    """Create 10 drone bases across India."""
    print("\nCreating drone bases...")
    bases = []

    for idx, base_data in enumerate(INDIAN_BASES, 1):
        base = DroneBase(
            base_id=f"BASE-IND-{idx:03d}",  # India country code with sequential number
            name=base_data["name"],
            location={
                "type": "Point",
                "coordinates": [base_data["lng"], base_data["lat"]],
            },
            address=base_data["address"],
            region=base_data["region"],
            status=random.choice(
                ["active", "active", "active", "maintenance"]
            ),  # 75% active
            max_drones=50,  # Fixed at 50 max drones per base
            operational_radius=random.uniform(10.0, 15.0),  # 10-15km operational range
        )
        base.save()
        bases.append(base)
        print(f"  ✓ Created {base.name} ({base.base_id}) in {base_data['city']}")

    print(f"✓ Created {len(bases)} drone bases")
    return bases


def seed_drones(bases):
    """Create 30-45 drones per base."""
    print("\nCreating drones...")

    all_drones = []
    used_ids = set()

    for base in bases:
        # Random number of drones for this base (30-45)
        num_drones_for_base = random.randint(30, 45)
        base_coords = base.location["coordinates"]  # [lng, lat]

        print(f"\n  Creating {num_drones_for_base} drones for {base.name}...")

        for i in range(num_drones_for_base):
            # Simple name with base prefix and counter
            prefix = random.choice(DRONE_PREFIXES)
            suffix = random.choice(
                ["Scout", "Patrol", "Mapper", "Surveyor", "Guard", "Watcher"]
            )
            name = f"{prefix} {suffix}"

            # Generate unique ID
            while True:
                drone_id = generate_drone_id()
                if drone_id not in used_ids:
                    used_ids.add(drone_id)
                    break

            # Random model
            drone_model = random.choice(DRONE_MODELS)

            # All drones are available
            status = "available"

            # All drones have 100% battery
            battery_level = 100.0

            # At base location
            location = {"lat": base_coords[1], "lng": base_coords[0], "alt": 0.0}

            # Home base
            home_base = {"lat": base_coords[1], "lng": base_coords[0], "alt": 0.0}

            # Flight hours and health
            total_flight_hours = random.uniform(10, 500)
            if total_flight_hours > 400:
                health_status = random.choice(["good", "warning"])
            elif total_flight_hours > 300:
                health_status = random.choice(["good", "good", "warning"])
            else:
                health_status = "good"

            # Last maintenance
            days_ago = random.randint(1, 90)
            last_maintenance = (
                datetime.utcnow() - timedelta(days=days_ago)
            ).isoformat()

            drone = Drone(
                drone_id=drone_id,
                name=name,
                model=drone_model["model"],
                manufacturer=drone_model["manufacturer"],
                status=status,
                battery_level=battery_level,
                location=location,
                home_base=home_base,
                assigned_site=base.name,
                base_id=base.base_id,
                max_flight_time=random.randint(25, 45),
                max_speed=random.uniform(12.0, 20.0),
                max_altitude=random.uniform(100.0, 150.0),
                payload_capacity=random.uniform(0.3, 2.0),
                total_flight_hours=total_flight_hours,
                last_maintenance=last_maintenance,
                health_status=health_status,
                camera_specs={
                    "resolution": random.choice(["4K", "5.1K", "8K"]),
                    "sensor": random.choice(
                        ["1-inch CMOS", "1/2-inch CMOS", "Micro Four Thirds"]
                    ),
                    "zoom": random.choice(["2x", "4x", "8x", "16x"]),
                },
            )
            drone.save()
            all_drones.append(drone)

        print(f"  ✓ Created {num_drones_for_base} drones at {base.name}")

    print(f"\n✓ Created {len(all_drones)} total drones across all bases")
    return all_drones


def print_summary(bases, drones):
    """Print summary of seeded data."""
    print("\n" + "=" * 60)
    print("SEEDING SUMMARY")
    print("=" * 60)

    print(f"\nBases Created: {len(bases)}")
    for base in bases:
        drone_count = len([d for d in drones if d.assigned_site == base.name])
        print(f"  • {base.name} ({base.base_id}): {drone_count} drones")

    print(f"\nDrones Created: {len(drones)}")
    status_counts = {}
    for drone in drones:
        status_counts[drone.status] = status_counts.get(drone.status, 0) + 1

    for status, count in sorted(status_counts.items()):
        percentage = (count / len(drones)) * 100
        print(f"  • {status}: {count} ({percentage:.1f}%)")

    print("\n" + "=" * 60)
    print("✓ Seeding completed successfully!")
    print("=" * 60)


def main():
    """Main seeding function."""
    print("=" * 60)
    print("DRONE FLEET SEEDING - INDIA")
    print("=" * 60)

    try:
        # Clear existing data
        clear_existing_data()

        # Seed bases
        bases = seed_bases()

        # Seed drones
        drones = seed_drones(bases)

        # Print summary
        print_summary(bases, drones)

    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
