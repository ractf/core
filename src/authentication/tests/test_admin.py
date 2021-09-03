"""Tests for admin only authentication api routes."""

from django.http import HttpRequest
from django.urls import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APITestCase

from authentication import views
from member.models import Member
from teams.models import Team


class SudoTestCase(APITestCase):
    """Tests for the sudo view."""

    def test_sudo(self):
        """Sudo as a user should return 200."""
        user = Member(username="sudotest", is_staff=True, email="sudotest@example.com", is_superuser=True)
        user.save()
        user2 = Member(username="sudotest2", email="sudotest2@example.com")
        user2.save()

        self.client.force_authenticate(user)
        req = self.client.post(reverse("sudo"), {"id": user2.pk})
        self.assertEqual(req.status_code, status.HTTP_200_OK)


class DeSudoTestCase(APITestCase):
    """Tests for the desudo view."""

    def test_desudo(self):
        """Dropping sudo should return 200."""
        user2 = Member(username="sudotest2", email="sudotest2@example.com")
        user2.save()

        request = Request(HttpRequest())
        request.sudo_from = user2

        response = views.DesudoView().post(request)
        self.assertTrue("token" in response.data["d"])


class CreateBotUserTestCase(APITestCase):
    """Tests for creating a bot user."""

    def setUp(self):
        """Create a staff user for use in tests."""
        user = Member(username="bot-test", email="bot-test@example.org", is_staff=True, is_superuser=True)
        user.set_password("password")
        user.save()
        self.user = user
        views.CreateBotView.throttle_scope = ""

    def test_unauthenticated(self):
        """An unauthenticated user should not be able to make a bot."""
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_admin(self):
        """An admin user should not be able to make a bot."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_authenticated_not_admin(self):
        """A non-admin user should not be able to make a bot."""
        self.user.is_staff = False
        self.user.is_superuser = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_issues_token(self):
        """Creating a bot user should return the bot's token."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.assertTrue("token" in response.data["d"])


class GenerateInvitesTestCase(APITestCase):
    """Tests for generating invite codes."""

    def test_response_length(self):
        """Test the specified amount of invite codes are generated."""
        user = Member(username="resend-email", is_staff=True, email="tvu@example.com", is_superuser=True)
        user.save()
        self.client.force_authenticate(user=user)
        team = Team.objects.create(owner=user, name=user.username, password="123123")
        response = self.client.post(reverse("generate-invites"), {"amount": 15, "auto_team": team.pk, "max_uses": 1})
        self.assertEqual(len(response.data["d"]["invite_codes"]), 15)

    def test_invites_viewset(self):
        """Test the invite codes are listed correctly."""
        user = Member(username="resend-email", is_staff=True, email="tvu@example.com", is_superuser=True)
        user.save()
        self.client.force_authenticate(user=user)
        self.client.post(reverse("generate-invites"), {"amount": 15, "max_uses": 1})
        response = self.client.get(reverse("invites-list"))
        self.assertEqual(len(response.data["d"]["results"]), 15)
