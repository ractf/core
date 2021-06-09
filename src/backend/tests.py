from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from backend.permissions import ReadOnlyBot
from member.models import Member


class CatchAllTestCase(APITestCase):
    def test_catchall_404s(self):
        response = self.client.get("/sdgodgsjds")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)


class ReadOnlyBotTestCase(APITestCase):
    def test_is_bot_safe_method(self):
        request = Request(HttpRequest())
        request.method = "GET"
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertTrue(ReadOnlyBot().has_permission(request, None))

    def test_is_bot_unsafe_method(self):
        request = Request(HttpRequest())
        request.method = "POST"
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertFalse(ReadOnlyBot().has_permission(request, None))
