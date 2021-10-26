"""Tests for the member app."""

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from rest_framework.test import APITestCase

from core.tests.utils import patch_config
from teams.models import Team, UserIP, Member


class MemberTestCase(APITestCase):
    """Tests for the member-self api endpoint."""

    def setUp(self):
        """Create a user for use in unit tests."""
        user = Member(username="test-self", email="test-self@example.org")
        user.save()
        self.user = user

    def test_str(self):
        """Test the string representation of a user."""
        user = Member(username="test-str", email="test-str@example.org")
        self.assertEqual(str(user), user.username)

    def test_self_status(self):
        """Test member-self can be accessed by an authenticated user."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-self"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_self_status_unauth(self):
        """Test member-self cannot be accessed by an unauthenticated user."""
        response = self.client.get(reverse("member-self"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_self_change_email(self):
        """Test email can be changed."""
        self.client.force_authenticate(self.user)
        response = self.client.put(
            reverse("member-self"), data={"email": "test-self2@example.org", "username": "test-self"}
        )
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test-self2@example.org")

    def test_self_change_email_invalid(self):
        """Test email cannot be changed to an invalid email."""
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse("member-self"), data={"email": "test-self"})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_self_change_email_token_change(self):
        """Test changing email changes email verification token."""
        ev_token = self.user.email_token
        self.client.force_authenticate(self.user)
        self.client.put(reverse("member-self"), data={"email": "test-self3@example.org"})
        self.user.refresh_from_db()
        self.assertNotEqual(ev_token, self.user.email_token)

    def test_self_get_email(self):
        """Test a user can get their email."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-self"))
        self.assertEqual(response.data["email"], "test-self@example.org")

    @patch_config(enable_teams=False)
    def test_self_change_username_teams_disabled(self, config_get):
        """Test changing username changed the name of the users team when teams are disabled."""
        self.client.force_authenticate(self.user)
        team = Team(name="team", password="123", owner=self.user)
        team.save()
        self.user.team = team
        self.user.save()
        self.client.put(reverse("member-self"), data={"username": "test-self2", "email": "test-self@example.org"})
        team.refresh_from_db()
        self.assertEqual(team.name, "test-self2")
        self.assertTrue(config_get.called_once)

    @patch_config(enable_teams=False)
    def test_self_change_username_no_team(self, config_get):
        """Test changing username with teams disabled changes the username."""
        self.client.force_authenticate(self.user)
        self.client.put(reverse("member-self"), data={"username": "test-self2", "email": "test-self@example.org"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "test-self2")
        self.assertTrue(config_get.called_once)


class MemberViewSetTestCase(APITestCase):
    """Tests for MemberViewset."""

    def setUp(self):
        """Create a test user and a test admin user."""
        user = Member(username="test-member", email="test-member@example.org")
        user.save()
        self.user = user
        user = Member(username="test-admin", email="test-admin@example.org")
        user.is_staff = True
        user.save()
        self.admin_user = user

    def test_visible_admin(self):
        """Test admins can see all users."""
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("member-list"))
        self.assertEqual(len(response.data["d"]["results"]), 3)

    def test_visible_not_admin(self):
        """Test non admins can only see visible users."""
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-list"))
        self.assertEqual(len(response.data["d"]["results"]), 0)

    def test_visible_detail_admin(self):
        """Test admins can view details of a not visible user."""
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": user.pk}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_visible_detail_not_admin(self):
        """Test non admins cannot view details of a not visible user."""
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": user.pk}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_view_email_admin(self):
        """Test admins can view user emails."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": self.user.pk}))
        self.assertTrue("email" in response.data)

    def test_view_email_not_admin(self):
        """Test non-admins cant view user emails."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": self.admin_user.pk}))
        self.assertFalse("email" in response.data)

    def test_view_member(self):
        """Test users can view visible members."""
        self.admin_user.is_visible = True
        self.admin_user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": self.admin_user.pk}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_patch_member(self):
        """Test non-admin users cant patch other users."""
        self.admin_user.is_visible = True
        self.admin_user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("member-detail", kwargs={"pk": self.admin_user.pk}),
            data={"username": "test"},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_patch_member_admin(self):
        """Test admins can patch other users."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.patch(
            reverse("member-detail", kwargs={"pk": self.user.pk}),
            data={"username": "test"},
        )
        self.assertEqual(response.status_code, HTTP_200_OK)


class UserIPTest(APITestCase):
    """Tests for the UserIP model."""

    def test_not_authenticated(self):
        """Test unauthenticated users do not get logged."""
        request = Request(HttpRequest())
        request.user = AnonymousUser()
        self.assertNumQueries(0, lambda: UserIP.hook(request))

    def test_first_sight(self):
        """Test authenticated users get logged."""
        request = Request(HttpRequest())
        user = Member(username="test-userip", email="test-userip@example.org")
        user.save()
        request.user = user
        request.META["x-forward-for"] = "1.1.1.1"
        request.META["user-agent"] = "test"
        UserIP.hook(request)
        self.assertEqual(UserIP.objects.get(user=user).seen, 1)

    def test_second_sight(self):
        """Test the seen attribute is correctly incrememented."""
        request = Request(HttpRequest())
        user = Member(username="test-userip2", email="test-userip2@example.org")
        user.save()
        request.user = user
        request.META["x-forward-for"] = "1.1.1.1"
        request.META["user-agent"] = "test"
        UserIP.hook(request)
        UserIP.hook(request)
        self.assertEqual(UserIP.objects.get(user=user).seen, 2)
