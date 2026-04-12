"""
ASGI config for edupath project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupath.settings')
application = get_asgi_application()
