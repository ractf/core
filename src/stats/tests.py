from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from challenge.models import Category, Challenge, Solve
from config import config
from team.models import Team


class CountdownTestCase(APITestCase):
    def test_unauthed(self):
        response = self.client.get(reverse("countdown"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        user = get_user_model()(username="countdown-test", email="countdown-test@example.org")
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("countdown"))
        self.assertEqual(response.status_code, HTTP_200_OK)


class StatsTestCase(APITestCase):
    def test_unauthed(self):
        response = self.client.get(reverse("stats"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        user = get_user_model()(username="stats-test", email="stats-test@example.org")
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("stats"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_team_average(self):
        user = get_user_model()(username="stats-test", email="stats-test@example.org")
        user.save()

        team = Team(name="stats-test", password="stats-test", owner=user)
        team.save()

        response = self.client.get(reverse("stats"))
        self.assertEqual(response.data["d"]["avg_members"], 1)


class FullStatsTestCase(APITestCase):
    def test_unauthed(self):
        response = self.client.get(reverse("full"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authed_non_privileged(self):
        user = get_user_model()(username="stats-test", email="stats-test@example.org")
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("full"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_authed(self):
        user = get_user_model()(username="stats-test", email="stats-test@example.org", is_superuser=True, is_staff=True)
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("full"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_team_point_distribution(self):
        user = get_user_model()(username="stats-test", email="stats-test@example.org", is_superuser=True, is_staff=True)
        user.save()

        team = Team(name="stats-test", password="stats-test", owner=user)
        team.save()

        team1 = Team(name="stats-test1", password="stats-test", owner=user)
        team1.save()

        team2 = Team(name="stats-test2", password="stats-test", owner=user)
        team2.points = 5
        team2.save()

        self.client.force_authenticate(user)
        response = self.client.get(reverse("full"))
        self.assertEqual(response.data["d"]["team_point_distribution"][0], 2)
        self.assertEqual(response.data["d"]["team_point_distribution"][5], 1)

    def test_challenge_data(self):
        user = get_user_model()(username="stats-test", email="stats-test@example.org", is_superuser=True, is_staff=True)
        user.save()

        category = Category.objects.create(
            name="test category", display_order=1, contained_type="test", description="test"
        )
        chall = Challenge.objects.create(
            name="test challenge",
            category=category,
            challenge_metadata={},
            description="test challenge",
            challenge_type="test challenge",
            flag_type="none",
            flag_metadata={},
            author="test author",
            score=5,
        )

        Solve.objects.create(challenge=chall, flag="", correct=True)
        Solve.objects.create(challenge=chall, flag="", correct=False)

        self.client.force_authenticate(user)
        config.set("enable_caching", False)
        response = self.client.get(reverse("full"))
        config.set("enable_caching", True)
        self.assertEqual(response.data["d"]["challenges"][chall.id]["incorrect"], 1)
        self.assertEqual(response.data["d"]["challenges"][chall.id]["correct"], 1)


class CommitTestCase(APITestCase):
    def test_unauthed(self):
        response = self.client.get(reverse("version"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        user = get_user_model()(username="commit-test", email="commit-test@example.org")
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("version"))
        self.assertEqual(response.status_code, HTTP_200_OK)


class PrometheusTestCase(APITestCase):
    def test_unauthed(self):
        response = self.client.get(reverse("prometheus"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authed(self):
        user = get_user_model()(username="prometheus-test", email="prometheus-test@example.org")
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("prometheus"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_authed_admin(self):
        user = get_user_model()(
            username="prometheus-test-admin",
            email="prometheus-test-admin@example.org",
            is_staff=True,
            is_superuser=True,
        )
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("prometheus"))
        self.assertEqual(response.status_code, HTTP_200_OK)
