from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

from sockets import consumers

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    re_path(r"^ws/$", consumers.EventConsumer.as_asgi()),
                    re_path(r"^api/v2/ws/$", consumers.EventConsumer.as_asgi()),
                ]
            )
        )
    }
)
