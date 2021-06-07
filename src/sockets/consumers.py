import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from authentication.models import Token
from backend.signals import websocket_connect, websocket_disconnect


class EventConsumer(AsyncJsonWebsocketConsumer):
    groups = ["event"]

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("event", self.channel_name)
        await self.send_json({"event_code": 0, "message": "Websocket connected."})
        websocket_connect.send(self.__class__, channel_layer=self.channel_layer)

    async def disconnect(self, close_code):
        websocket_disconnect.send(self.__class__, channel_layer=self.channel_layer)

    @staticmethod
    def get_team(token):
        if not Token.objects.filter(key=token).exists():
            return None
        user = Token.objects.get(key=token).user
        return user.team

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        try:
            data = json.loads(text_data)
        except json.decoder.JSONDecodeError:
            return
        if "token" in data:
            team = await sync_to_async(self.get_team)(data["token"])
            if team is not None:
                await self.channel_layer.group_add(f"team.{team.id}", self.channel_name)
