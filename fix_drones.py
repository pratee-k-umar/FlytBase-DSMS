#!/usr/bin/env python
"""
Fix stale drone statuses
"""
import os
import sys

# Add src/dsms to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "dsms"))

from db import connect_db

connect_db()

from services.fleet_service import fix_stale_drone_statuses

count = fix_stale_drone_statuses()
print(f"\n✓ Fixed {count} drones with stale statuses\n")
