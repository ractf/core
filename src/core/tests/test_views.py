"""Tests for the views in the core app."""

import hashlib

from django.urls import reverse
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase

from challenges.models import Category, Challenge
from teams.models import Member


class CatchAllTestCase(APITestCase):
    """Tests for the catchall view."""

    def test_catchall_404s(self):
        """The view should return 404."""
        response = self.client.get("/sdgodgsjds")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)


class MissingPointsTestCase(APITestCase):
    """Test for the missing points case of the selfcheck endpoint."""

    def setUp(self):
        """Create a member for testing."""
        self.user = Member.objects.create(username="test", is_superuser=True, is_staff=True)
        self.category = Category.objects.create(name="test", display_order=0, contained_type="test", description="")
        self.challenge = Challenge.objects.create(
            name="test1",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}"},
            author="dave",
            score=0,
        )

    def test_missing_points(self):
        """A challenge with 0 points should flag a warning."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("self-check"))
        self.assertEqual(response.data["d"][0]["issue"], "missing_points")

    def test_not_missing_points(self):
        """A challenge with a non zero points value should not flag a warning."""
        self.challenge.score = 5
        self.challenge.save()
        response = self.client.get(reverse("self-check"))
        self.assertEqual(len(response.data["d"]), 0)


class BadFlagConfigTestCase(APITestCase):
    """Test the invalid flag case of the selfcheck endpoint."""

    def setUp(self):
        """Create users and challenges to use in the tests."""
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
        """Create a challenge."""
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
        """The endpoint should find 14 errors in the challenges."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("self-check"))
        self.assertEqual(len(response.data["d"]), 14)


class ExperimentsTestCase(APITestCase):
    """Test the experiments viewset."""

    def test_experiments(self):
        """Test the overrides are correctly sent."""
        with self.settings(EXPERIMENT_OVERRIDES={"test": True}):
            response = self.client.get(reverse("experiments"))
            self.assertEqual(response.data["d"]["test"], True)
