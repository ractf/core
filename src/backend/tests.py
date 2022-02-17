from unittest import TestCase

from django.core.exceptions import ValidationError
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from backend.pagination import prepend_api_prefix
from backend.permissions import ReadOnlyBot
from backend.validators import printable_name
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


class ValidatorTestCase(APITestCase):
    def test_unprintable_name(self):
        self.assertRaises(ValidationError, lambda: printable_name(b"\x00".decode("latin-1")))

    def test_printable_name(self):
        self.assertIsNone(printable_name("abc"))


class APIPrefixTestCase(TestCase):
    def test_prepend_api_prefix(self):
        prepended = prepend_api_prefix("https://api.ractf.co.uk/challenges/")
        self.assertEqual(prepended, "https://api.ractf.co.uk/api/v2/challenges/?")
