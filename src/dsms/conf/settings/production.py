"""
Production settings for DSMS.
"""

import os

from .base import *

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# Security settings
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS - restrict in production
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") 
    if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = False

# Static files - use WhiteNoise for serving
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

print("[PRODUCTION] Running with PRODUCTION settings")

