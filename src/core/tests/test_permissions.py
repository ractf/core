from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.test import APITestCase

from core.permissions import ReadOnlyBot
from member.models import Member


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
