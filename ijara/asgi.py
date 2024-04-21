"""
ASGI config for ijara project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack

from .middlewares import JwtAuthMiddlewareStack
from .socket_urls import websocket_urlpatterns

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ijara.settings')
django.setup()
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddlewareStack(
          URLRouter(
                websocket_urlpatterns
          )
      ),
    # Just HTTP for now. (We can add other protocols later.)
})