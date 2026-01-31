"""
WSGI config for DSMS project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsms.conf.settings.production")

application = get_wsgi_application()
