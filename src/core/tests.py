import hashlib

from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.urls import reverse
from rest_framework.request import Request
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from challenge.models import Category, Challenge
from core.permissions import ReadOnlyBot
from core.validators import printable_name
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


class MissingPointsTestCase(APITestCase):
    def setUp(self):
        self.user = Member.objects.create(username="test", is_superuser=True, is_staff=True)

    def test_missing_points(self):
        category = Category(name="test", display_order=0, contained_type="test", description="")
        category.save()
        x = Challenge.objects.create(
            name="test1",
            category=category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}"},
            author="dave",
            score=0,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("self-check"))
        self.assertEqual(response.data["d"][0]["issue"], "missing_points")

        x.score = 5
        x.save()
        response = self.client.get(reverse("self-check"))
        self.assertEqual(len(response.data["d"]), 0)


class BadFlagConfigTestCase(APITestCase):
    def setUp(self):
        self.user = Member.objects.create(username="test", is_superuser=True, is_staff=True)

        self.category = Category(name="test", display_order=0, contained_type="test", description="")
        self.category.save()
        self.i = 0

        self.create_challenge("hashed", {"not_flag": ""})
        self.create_challenge("hashed", {"flag": "invalid_flag"})
        self.create_challenge("hashed", {"flag": hashlib.sha256("bruh".encode("utf-8")).hexdigest()})

        self.create_challenge("plaintext", {"not_flag": ""})
        self.create_challenge("plaintext", {"flag": "meme"})
        self.create_challenge("plaintext", {"flag": "ractf{flag}"})

        self.create_challenge("lenient", {"not_flag": ""})
        self.create_challenge("lenient", {"flag": "meme"})
        self.create_challenge("lenient", {"flag": "ractf{flag}"})

        self.create_challenge("map", {"not_radius": ""})
        self.create_challenge("map", {"radius": "not a number"})
        self.create_challenge("map", {"location": "not a list"})
        self.create_challenge("map", {"location": [1, 2, 3, 4]})

        self.create_challenge("regex", {"not_flag": ""})
        self.create_challenge("regex", {"flag": "ractf{flag}"})

        self.create_challenge("long_text", {"not_flag": ""})
        self.create_challenge("long_text", {"flag": "ractf{flag}"})

    def create_challenge(self, typ, metadata):
        self.i += 1
        Challenge.objects.create(
            name=f"{self.i}",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type=typ,
            flag_metadata=metadata,
            author="dave",
            score=1,
        )

    def test_length(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("self-check"))
        self.assertEqual(len(response.data["d"]), 14)
