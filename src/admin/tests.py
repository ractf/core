import hashlib

from django.urls import reverse
from rest_framework.test import APITestCase

from challenge.models import Category, Challenge
from member.models import Member


class MissingPointsTestCase(APITestCase):
    def setUp(self):
        self.user = Member.objects.create(username="test", is_superuser=True, is_staff=True)

    def test_missing_points(self):
        category = Category(name="test", display_order=0, contained_type="test", description="")
        category.save()
        x = Challenge.objects.create(
            name="test1", category=category, description="a", challenge_type="basic", challenge_metadata={}, flag_type="plaintext", flag_metadata={"flag": "ractf{a}"}, author="dave", score=0
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
            name=f"{self.i}", category=self.category, description="a", challenge_type="basic", challenge_metadata={}, flag_type=typ, flag_metadata=metadata, author="dave", score=1
        )

    def test_length(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("self-check"))
        self.assertEqual(len(response.data["d"]), 14)
