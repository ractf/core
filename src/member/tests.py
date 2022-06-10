from django.contrib.auth.models import AnonymousUser
from django.db.utils import IntegrityError
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

from config import config
from member.models import UserIP, Member
from team.models import Team


class MemberTestCase(APITestCase):
    def setUp(self):
        user = Member(username="test-self", email="test-self@example.org")
        user.save()
        self.user = user

    def test_str(self):
        user = Member(username="test-str", email="test-str@example.org")
        self.assertEqual(str(user), user.username)

    def test_self_status(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-self"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_self_status_unauth(self):
        response = self.client.get(reverse("member-self"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_self_change_email(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(
            reverse("member-self"), data={"email": "test-self2@example.org", "username": "test-self"}
        )
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(Member.objects.get(id=self.user.id).email, "test-self2@example.org")

    def test_self_change_email_invalid(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse("member-self"), data={"email": "test-self"})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_self_change_email_token_change(self):
        ev_token = self.user.email_token
        self.client.force_authenticate(self.user)
        self.client.put(reverse("member-self"), data={"email": "test-self3@example.org"})
        user = Member.objects.get(id=self.user.id)
        self.assertNotEqual(ev_token, user.email_token)

    def test_self_get_email(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-self"))
        self.assertEqual(response.data["email"], "test-self@example.org")

    def test_self_change_username_teams_disabled(self):
        self.client.force_authenticate(self.user)
        team = Team(name="team", password="123", owner=self.user)
        team.save()
        self.user.team = team
        self.user.save()
        config.set("enable_teams", False)
        self.client.put(reverse("member-self"), data={"username": "test-self2", "email": "test-self@example.org"})
        config.set("enable_teams", True)
        self.assertEqual(Team.objects.get(id=team.id).name, "test-self2")

    def test_self_change_username_no_team(self):
        self.client.force_authenticate(self.user)
        config.set("enable_teams", False)
        self.client.put(reverse("member-self"), data={"username": "test-self2", "email": "test-self@example.org"})
        config.set("enable_teams", True)
        self.assertEqual(Member.objects.get(id=self.user.id).username, "test-self2")


class MemberViewSetTestCase(APITestCase):
    def setUp(self):
        user = Member(username="test-member", email="test-member@example.org")
        user.save()
        self.user = user
        user = Member(username="test-admin", email="test-admin@example.org")
        user.is_staff = True
        user.save()
        self.admin_user = user

    def test_visible_admin(self):
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("member-list"))
        self.assertEqual(len(response.data["d"]["results"]), 3)

    def test_visible_not_admin(self):
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-list"))
        self.assertEqual(len(response.data["d"]["results"]), 0)

    def test_visible_detail_admin(self):
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": user.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_visible_detail_not_admin(self):
        user = Member(username="test-member-invisible", email="test-member-invisible@example.org")
        user.is_visible = False
        user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": user.id}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_view_email_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": self.user.id}))
        self.assertTrue("email" in response.data)

    def test_view_email_not_admin(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": self.admin_user.id}))
        self.assertFalse("email" in response.data)

    def test_view_member(self):
        self.admin_user.is_visible = True
        self.admin_user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("member-detail", kwargs={"pk": self.admin_user.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_patch_member(self):
        self.admin_user.is_visible = True
        self.admin_user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("member-detail", kwargs={"pk": self.admin_user.id}),
            data={"username": "test"},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_disallows_differently_cased_but_same_username(self):
        """A differently-cased but otherwise same username should not be allowed registration."""

        self.user.username = self.admin_user.username.upper()
        self.assertRaises(IntegrityError, self.user.save)

    def test_patch_member_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.patch(
            reverse("member-detail", kwargs={"pk": self.user.id}),
            data={"username": "test"},
        )
        self.assertEqual(response.status_code, HTTP_200_OK)


class UserIPTest(APITestCase):
    def test_not_authenticated(self):
        request = Request(HttpRequest())
        request.user = AnonymousUser()
        self.assertNumQueries(0, lambda: UserIP.hook(request))

    def test_first_sight(self):
        request = Request(HttpRequest())
        user = Member(username="test-userip", email="test-userip@example.org")
        user.save()
        request.user = user
        request.META["x-forward-for"] = "1.1.1.1"
        request.META["user-agent"] = "test"
        UserIP.hook(request)
        self.assertEqual(UserIP.objects.get(user=user).seen, 1)

    def test_second_sight(self):
        request = Request(HttpRequest())
        user = Member(username="test-userip2", email="test-userip2@example.org")
        user.save()
        request.user = user
        request.META["x-forward-for"] = "1.1.1.1"
        request.META["user-agent"] = "test"
        UserIP.hook(request)
        UserIP.hook(request)
        self.assertEqual(UserIP.objects.get(user=user).seen, 2)
