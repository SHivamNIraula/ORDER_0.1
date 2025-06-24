"""
EMERGENCY ASGI CONFIG: Completely isolate WebSocket from HTTP
Place this in order_mng/asgi.py
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_mng.settings')

# Get Django ASGI application
django_asgi_app = get_asgi_application()

# Import routing
from payment import routing

class EmergencyWebSocketIsolation:
    """
    EMERGENCY: Completely isolate WebSocket from HTTP sessions
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            print("🚨 EMERGENCY: WebSocket isolated from HTTP sessions")
            
            # Create completely isolated scope
            isolated_scope = {
                "type": "websocket",
                "scheme": scope.get("scheme", "ws"),
                "path": scope.get("path", ""),
                "query_string": scope.get("query_string", b""),
                "headers": scope.get("headers", []),
                "client": scope.get("client", ["127.0.0.1", 0]),
                "server": scope.get("server", ["127.0.0.1", 8000]),
                "url_route": scope.get("url_route", {}),
                # CRITICAL: No session, no user, no auth
                "session": {},
                "user": None,
                "cookies": {},
            }
            
            return await self.inner(isolated_scope, receive, send)
        else:
            # HTTP requests proceed normally
            return await self.inner(scope, receive, send)

# EMERGENCY APPLICATION CONFIG
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": EmergencyWebSocketIsolation(
        URLRouter(routing.websocket_urlpatterns)
    ),
})