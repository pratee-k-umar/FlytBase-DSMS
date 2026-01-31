"""
MongoDB connection setup using MongoEngine.
Sentry pattern: Single connection point, imported at startup.
"""

import os

from dotenv import load_dotenv
from mongoengine import connect, disconnect

load_dotenv()

_connected = False


def connect_db():
    """Connect to MongoDB with retry logic"""
    global _connected
    if _connected:
        return

    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/dsms")
    connect(
        host=mongodb_uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=20000,
        socketTimeoutMS=20000,
        retryWrites=True,
        retryReads=True,
        maxPoolSize=50,
        minPoolSize=10,
    )
    _connected = True
    print(f"[OK] Connected to MongoDB")


def disconnect_db():
    """Disconnect from MongoDB"""
    global _connected
    disconnect()
    _connected = False
