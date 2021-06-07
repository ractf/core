import random

from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_200_OK, HTTP_401_UNAUTHORIZED
from rest_framework.test import APITestCase

from challenge.models import Score
from team.models import Team


class RecalculateUserViewTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="recalculate-test", email="recalculate-test@example.org")
        user.save()
        admin_user = get_user_model()(
            username="recalculate-test-admin",
            email="recalculate-test-admin@example.org",
        )
        admin_user.is_staff = True
        admin_user.save()
        team = Team(name="recalculate-team", owner=user, password="a")
        team.save()
        user.team = team
        user.save()
        self.user = user
        self.admin_user = admin_user
        self.team = team

    def test_unauthed(self):
        response = self.client.post(reverse("recalculate-user", kwargs={"id": self.user.id}))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authed(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("recalculate-user", kwargs={"id": self.user.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed_not_admin(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("recalculate-user", kwargs={"id": self.user.id}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_recalculate(self):
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("recalculate-user", kwargs={"id": self.user.id}))
        self.assertEqual(get_user_model().objects.get(id=self.user.id).points, total + 100)

    def test_recalculate_leaderboard(self):
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("recalculate-user", kwargs={"id": self.user.id}))
        self.assertEqual(get_user_model().objects.get(id=self.user.id).leaderboard_points, total)


class RecalculateTeamViewTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="recalculate-test", email="recalculate-test@example.org")
        user.save()
        admin_user = get_user_model()(
            username="recalculate-test-admin",
            email="recalculate-test-admin@example.org",
        )
        admin_user.is_staff = True
        admin_user.save()
        team = Team(name="recalculate-team", owner=user, password="a")
        team.save()
        user.team = team
        user.save()
        self.user = user
        self.admin_user = admin_user
        self.team = team

    def test_unauthed(self):
        response = self.client.post(reverse("recalculate-team", kwargs={"id": self.team.id}))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authed(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("recalculate-team", kwargs={"id": self.team.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed_not_admin(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("recalculate-team", kwargs={"id": self.team.id}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_recalculate(self):
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("recalculate-team", kwargs={"id": self.team.id}))
        self.assertEqual(Team.objects.get(id=self.team.id).points, total + 100)

    def test_recalculate_leaderboard(self):
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("recalculate-team", kwargs={"id": self.team.id}))
        self.assertEqual(Team.objects.get(id=self.team.id).leaderboard_points, total)


class RecalculateAllViewTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="recalculate-test", email="recalculate-test@example.org")
        user.save()
        admin_user = get_user_model()(
            username="recalculate-test-admin",
            email="recalculate-test-admin@example.org",
        )
        admin_user.is_staff = True
        admin_user.save()
        team = Team(name="recalculate-team", owner=user, password="a")
        team.save()
        user.team = team
        user.save()
        self.user = user
        self.admin_user = admin_user
        self.team = team

    def test_unauthed(self):
        response = self.client.post(reverse("recalculate-all"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authed(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("recalculate-all"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed_not_admin(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("recalculate-all"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_recalculate(self):
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("recalculate-all"))
        self.assertEqual(Team.objects.get(id=self.team.id).points, total + 100)
        self.assertEqual(get_user_model().objects.get(id=self.user.id).points, total + 100)

    def test_recalculate_leaderboard(self):
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("recalculate-all"))
        self.assertEqual(Team.objects.get(id=self.team.id).leaderboard_points, total)
        self.assertEqual(get_user_model().objects.get(id=self.user.id).leaderboard_points, total)
