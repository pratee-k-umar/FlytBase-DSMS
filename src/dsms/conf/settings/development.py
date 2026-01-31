"""
Development settings for DSMS.
"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1"]

# Use in-memory channel layer for development (no Redis needed)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# More verbose logging in development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

print("Running with DEVELOPMENT settings")
