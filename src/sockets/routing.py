from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, re_path

from sockets import consumers


application = ProtocolTypeRouter(
    {
        "http": AuthMiddlewareStack(
            URLRouter(
                [
                    path("ws/metrics", consumers.PrometheusConsumer.as_asgi()),
                    path("api/v2/ws/metrics", consumers.PrometheusConsumer.as_asgi()),
                ],
            ),
        ),
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
