"""
Seed script to populate database with DJI drone fleet across Indian bases.
Uses drone data from drone-data.json with images from drone-gallery folder.

Run from project root: python scripts/seed_drone_fleet.py
"""

import json
import os
import random
import sys
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

# Load drone data from JSON
DRONE_DATA_PATH = os.path.join(project_root, "drone-data.json")
with open(DRONE_DATA_PATH, "r") as f:
    DRONE_DATA = json.load(f)

# Map drone data to image files
DRONE_IMAGES = {
    "DJI Mavic 4 Pro": "dji-mavic-4-pro.png",
    "DJI Mavic 3 Pro": "dji-mavic-3-pro.png",
    "DJI Air 3S": "dji-air-3s.png",
    "DJI Mini 5 Pro": "dji-mini-5-pro.png",
    "DJI Mini 4 Pro": "dji-mini-4-pro.png",
    "DJI Mini 3": "dji-mini-3.png",
    "DJI Mini 2 SE": "dji-mini-2-se.png",
    "DJI Flip": "dji-flip.png",
    "DJI Neo 2": "dji-neo-2.png",
    "DJI Neo": "dji-neo.png",
    "DJI Avata 2": "dji-avata-2.png",
    "DJI Inspire 3": "dji-inspire-3.png",
}

# Parse drone data into a list of models
DRONE_MODELS = []
for category, drones in DRONE_DATA.items():
    for drone_id, drone_info in drones.items():
        model_name = drone_info["name"]
        DRONE_MODELS.append(
            {
                "model": model_name,
                "manufacturer": "DJI",
                "description": drone_info.get("description", ""),
                "image": DRONE_IMAGES.get(model_name, None),
                "category": category,
            }
        )

# Indian bases (existing bases in database)
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

# Drone name prefixes based on DJI categories
DRONE_PREFIXES = {
    "mavic": ["Alpha", "Beta", "Gamma", "Delta", "Sigma"],
    "air": ["Sky", "Cloud", "Aero", "Breeze", "Wind"],
    "mini": ["Swift", "Nimble", "Compact", "Micro", "Tiny"],
    "flip": ["Acro", "Twist", "Roll", "Spin", "Loop"],
    "neo": ["Nova", "Star", "Comet", "Meteor", "Orbit"],
    "avata": ["Falcon", "Hawk", "Eagle", "Raptor", "Phoenix"],
    "inspire": ["Titan", "Apex", "Prime", "Elite", "Master"],
}


def generate_drone_id():
    """Generate unique drone ID."""
    return f"DRN-{random.randint(1000, 9999)}-{random.randint(100, 999)}"


def get_drone_specs(model_info):
    """Extract specs from model description."""
    description = model_info.get("description", "")

    # Determine camera resolution
    if "8K" in description:
        resolution = "8K"
    elif "6K" in description:
        resolution = "6K"
    elif "5.1K" in description:
        resolution = "5.1K"
    elif "4K" in description:
        resolution = "4K"
    else:
        resolution = "4K"

    # Determine sensor size
    if "Full-Frame" in description or "1-inch" in description or "1″" in description:
        sensor = "1-inch CMOS"
    elif "4/3 CMOS" in description:
        sensor = "4/3 CMOS"
    elif "1/1.3" in description:
        sensor = "1/1.3-inch CMOS"
    elif "1/1.5" in description:
        sensor = "1/1.5-inch CMOS"
    elif "1/1.8" in description:
        sensor = "1/1.8-inch CMOS"
    else:
        sensor = "1/2.3-inch CMOS"

    # Flight time estimation based on category
    category = model_info.get("category", "mini")
    if category == "inspire":
        flight_time = random.randint(25, 28)
        max_speed = random.uniform(25.0, 30.0)
        payload = random.uniform(2.0, 3.0)
    elif category == "mavic":
        flight_time = random.randint(40, 51)
        max_speed = random.uniform(19.0, 21.0)
        payload = random.uniform(0.9, 1.5)
    elif category == "air":
        flight_time = random.randint(40, 45)
        max_speed = random.uniform(19.0, 21.0)
        payload = random.uniform(0.7, 1.2)
    elif category == "avata":
        flight_time = random.randint(18, 23)
        max_speed = random.uniform(25.0, 27.0)
        payload = random.uniform(0.3, 0.5)
    elif category in ["mini", "flip", "neo"]:
        flight_time = random.randint(28, 34)
        max_speed = random.uniform(15.0, 17.0)
        payload = random.uniform(0.1, 0.3)
    else:
        flight_time = random.randint(25, 35)
        max_speed = random.uniform(15.0, 20.0)
        payload = random.uniform(0.5, 1.0)

    return {
        "flight_time": flight_time,
        "max_speed": max_speed,
        "payload": payload,
        "camera": {
            "resolution": resolution,
            "sensor": sensor,
            "zoom": "Variable" if "zoom" in description.lower() else "Fixed",
        },
    }


def clear_existing_drones():
    """Clear existing drones only (keep bases)."""
    print("Clearing existing drones...")
    count = Drone.objects.delete()
    print(f"✓ Cleared {count} existing drones")


def seed_drones_for_bases():
    """Create drones for all existing bases in the database."""
    print("\nFetching existing bases from database...")
    bases = list(DroneBase.objects.all())

    if not bases:
        print("❌ No bases found in database. Please run seed_base_data.py first.")
        return []

    print(f"✓ Found {len(bases)} bases")
    print("\nCreating DJI drone fleet...")

    all_drones = []
    used_ids = set()

    for base in bases:
        # Random number of drones for this base (30-45)
        num_drones_for_base = random.randint(30, 45)
        base_coords = base.location["coordinates"]  # [lng, lat]

        print(f"\n  Creating {num_drones_for_base} drones for {base.name}...")

        for i in range(num_drones_for_base):
            # Randomly select a drone model
            model_info = random.choice(DRONE_MODELS)
            category = model_info["category"]

            # Generate name based on category
            prefixes = DRONE_PREFIXES.get(category, ["Unit"])
            name = f"{random.choice(prefixes)}-{random.randint(100, 999)}"

            # Generate unique ID
            while True:
                drone_id = generate_drone_id()
                if drone_id not in used_ids:
                    used_ids.add(drone_id)
                    break

            # Get specs for this model
            specs = get_drone_specs(model_info)

            # All drones are available with 100% battery
            status = "available"
            battery_level = 100.0

            # At base location
            location = {"lat": base_coords[1], "lng": base_coords[0], "alt": 0.0}
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

            # Image path (relative to static folder)
            image_path = (
                f"/static/drone-gallery/{model_info['image']}"
                if model_info.get("image")
                else None
            )

            drone = Drone(
                drone_id=drone_id,
                name=name,
                model=model_info["model"],
                manufacturer=model_info["manufacturer"],
                status=status,
                battery_level=battery_level,
                location=location,
                home_base=home_base,
                assigned_site=base.name,
                base_id=base.base_id,
                max_flight_time=specs["flight_time"],
                max_speed=specs["max_speed"],
                max_altitude=random.uniform(100.0, 150.0),
                payload_capacity=specs["payload"],
                total_flight_hours=total_flight_hours,
                last_maintenance=last_maintenance,
                health_status=health_status,
                camera_specs=specs["camera"],
                image_url=image_path,
            )
            drone.save()
            all_drones.append(drone)

        print(f"  ✓ Created {num_drones_for_base} DJI drones at {base.name}")

    print(f"\n✓ Created {len(all_drones)} total DJI drones across all bases")
    return all_drones


def print_summary(drones):
    """Print summary of seeded drones."""
    print("\n" + "=" * 60)
    print("DRONE FLEET SEEDING SUMMARY")
    print("=" * 60)

    # Count drones per base
    bases = DroneBase.objects.all()
    print(f"\nDrones per Base:")
    for base in bases:
        drone_count = len([d for d in drones if d.base_id == base.base_id])
        print(f"  • {base.name} ({base.base_id}): {drone_count} drones")

    # Count by model
    print(f"\nDrones by Model:")
    model_counts = {}
    for drone in drones:
        model_counts[drone.model] = model_counts.get(drone.model, 0) + 1

    for model, count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(drones)) * 100
        print(f"  • {model}: {count} ({percentage:.1f}%)")

    # Count by category
    print(f"\nDrones by Category:")
    category_counts = {}
    for drone in drones:
        # Determine category from model name
        model_lower = drone.model.lower()
        if "mavic" in model_lower:
            cat = "Mavic"
        elif "air" in model_lower:
            cat = "Air"
        elif "mini" in model_lower:
            cat = "Mini"
        elif "flip" in model_lower:
            cat = "Flip"
        elif "neo" in model_lower:
            cat = "Neo"
        elif "avata" in model_lower:
            cat = "Avata"
        elif "inspire" in model_lower:
            cat = "Inspire"
        else:
            cat = "Other"

        category_counts[cat] = category_counts.get(cat, 0) + 1

    for category, count in sorted(
        category_counts.items(), key=lambda x: x[1], reverse=True
    ):
        percentage = (count / len(drones)) * 100
        print(f"  • {category}: {count} ({percentage:.1f}%)")

    print(f"\nTotal Drones Created: {len(drones)}")

    print("\n" + "=" * 60)
    print("✓ DJI Fleet Seeding completed successfully!")
    print("=" * 60)


def main():
    """Main seeding function."""
    print("=" * 60)
    print("DJI DRONE FLEET SEEDING")
    print("=" * 60)
    print(f"Available Models: {len(DRONE_MODELS)}")
    for model in DRONE_MODELS:
        print(f"  • {model['model']} ({model['category']})")

    try:
        # Clear existing drones
        clear_existing_drones()

        # Seed drones for all existing bases
        drones = seed_drones_for_bases()

        if drones:
            # Print summary
            print_summary(drones)

    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
