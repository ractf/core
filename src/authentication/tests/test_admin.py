from django.http import HttpRequest
from django.urls import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APITestCase

from authentication import views
from member.models import Member
from team.models import Team


class SudoTestCase(APITestCase):
    def test_sudo(self):
        user = Member(username="sudotest", is_staff=True, email="sudotest@example.com", is_superuser=True)
        user.save()
        user2 = Member(username="sudotest2", email="sudotest2@example.com")
        user2.save()

        self.client.force_authenticate(user)
        req = self.client.post(reverse("sudo"), {"id": user2.pk})
        self.assertEqual(req.status_code, status.HTTP_200_OK)


class DeSudoTestCase(APITestCase):
    def test_desudo(self):
        user2 = Member(username="sudotest2", email="sudotest2@example.com")
        user2.save()

        request = Request(HttpRequest())
        request.sudo_from = user2

        response = views.DesudoView().post(request)
        self.assertTrue("token" in response.data["d"])


class CreateBotUserTestCase(APITestCase):
    def setUp(self):
        user = Member(username="bot-test", email="bot-test@example.org", is_staff=True, is_superuser=True)
        user.set_password("password")
        user.save()
        self.user = user
        views.CreateBotView.throttle_scope = ""

    def test_unauthenticated(self):
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
    def test_response_length(self):
        user = Member(username="resend-email", is_staff=True, email="tvu@example.com", is_superuser=True)
        user.save()
        self.client.force_authenticate(user=user)
        team = Team.objects.create(owner=user, name=user.username, password="123123")
        response = self.client.post(reverse("generate-invites"), {"amount": 15, "auto_team": team.pk, "max_uses": 1})
        self.assertEqual(len(response.data["d"]["invite_codes"]), 15)

    def test_invites_viewset(self):
        user = Member(username="resend-email", is_staff=True, email="tvu@example.com", is_superuser=True)
        user.save()
        self.client.force_authenticate(user=user)
        self.client.post(reverse("generate-invites"), {"amount": 15, "max_uses": 1})
        response = self.client.get(reverse("invites-list"))
        self.assertEqual(len(response.data["d"]["results"]), 15)
