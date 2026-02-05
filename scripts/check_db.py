"""
Quick check to verify database contents
"""

import os
import sys

# Add src directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsms.conf.settings.development")

from dsms.db import connect_db
connect_db()

from dsms.models.drone_base import DroneBase
from dsms.models.drone import Drone

print("=" * 60)
print("DATABASE CONTENTS CHECK")
print("=" * 60)

# Check bases
bases = DroneBase.objects()
print(f"\nTotal Bases: {bases.count()}")
for base in bases:
    print(f"\n  Base: {base.name} ({base.base_id})")
    print(f"  Location: {base.lat}, {base.lng}")
    print(f"  Status: {base.status}")
    print(f"  Max Drones: {base.max_drones}")
    print(f"  Operational Radius: {base.operational_radius}km")

# Check drones
drones = Drone.objects()
print(f"\n\nTotal Drones: {drones.count()}")

if drones.count() > 0:
    print("\nDrones by Base:")
    for base in bases:
        base_drones = Drone.objects(assigned_site=base.name)
        print(f"  {base.name}: {base_drones.count()} drones")
        for drone in base_drones[:3]:  # Show first 3
            print(f"    - {drone.name} ({drone.drone_id}) [{drone.status}]")
else:
    print("\n NO DRONES FOUND IN DATABASE!")
    print("\nChecking for any drones without assigned_site...")
    all_drones = Drone.objects()
    for drone in all_drones:
        print(f"  {drone.name} - assigned_site: {drone.assigned_site}")

print("\n" + "=" * 60)
