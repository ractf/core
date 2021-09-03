"""Websocket consumers used by the sockets app."""

import json

import prometheus_client
from asgiref.sync import sync_to_async
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from authentication.models import Token
from core.signals import websocket_connect, websocket_disconnect


class EventConsumer(AsyncJsonWebsocketConsumer):
    """The main websocket consumer for RACTF core."""

    groups = ["event"]

    async def connect(self):
        """Handle a websocket connection."""
        await self.accept()
        await self.channel_layer.group_add("event", self.channel_name)
        await self.send_json({"event_code": 0, "message": "Websocket connected."})
        websocket_connect.send(self.__class__, channel_layer=self.channel_layer)

    async def disconnect(self, close_code):
        """Handle a websocket disconnection."""
        websocket_disconnect.send(self.__class__, channel_layer=self.channel_layer)

    @staticmethod
    def get_team(token):
        """Return a user's team."""
        if not Token.objects.filter(key=token).exists():
            return None
        user = Token.objects.get(key=token).user
        return user.team

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        """Handle an incoming websocket message."""
        try:
            data = json.loads(text_data)
        except json.decoder.JSONDecodeError:
            return
        if "token" in data:
            team = await sync_to_async(self.get_team)(data["token"])
            if team is not None:
                await self.channel_layer.group_add(f"team.{team.pk}", self.channel_name)


class PrometheusConsumer(AsyncHttpConsumer):
    """Returns metrics for Prometheus via HTTP."""

    async def handle(self, body: str) -> None:
        """Export metrics in Prometheus format."""

        latest = prometheus_client.generate_latest(prometheus_client.REGISTRY)
        await self.send_response(
            200,
            latest,
            headers=[(b"Content-Type", prometheus_client.CONTENT_TYPE_LATEST.encode())],
        )
