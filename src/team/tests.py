from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.test import APITestCase

from challenge.models import Category, Challenge, Solve
from config import config
from team.models import Team


class TeamSetupMixin:
    def setUp(self):
        self.user = get_user_model()(username="team-test", email="team-test@example.org", is_visible=True)
        self.user.save()
        self.team = Team(name="team-test", password="abc", description="", owner=self.user, is_visible=True)
        self.team.save()
        self.user.team = self.team
        self.user.save()
        self.admin_user = get_user_model()(
            username="team-test-admin", email="team-test-admin@example.org", is_visible=True
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()


class TeamSelfTestCase(TeamSetupMixin, APITestCase):
    def test_team_self(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_team_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["password"], "abc")

    def test_no_team(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_not_authed(self):
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_update(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(reverse("team-self"), data={"name": "name-change"})
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["name"], "name-change")

    def test_update_not_owner(self):
        self.admin_user.team = self.team
        self.admin_user.is_staff = False
        self.admin_user.save()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(reverse("team-self"), data={"name": "name-change"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_team_leave_disabled(self):
        self.client.force_authenticate(user=self.user)
        config.set("enable_team_leave", False)
        response = self.client.post(reverse("team-leave"))
        config.set("enable_team_leave", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_team_leave_challenge_solved(self):
        config.set("enable_team_leave", True)
        self.client.force_authenticate(user=self.user)

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

        Solve.objects.create(solved_by=self.user, flag="", challenge=chall)
        response = self.client.post(reverse("team-leave"))
        config.set("enable_team_leave", False)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_team_leave_as_owner_with_members(self):
        self.client.force_authenticate(user=self.user)

        self.admin_user.team = self.team
        self.admin_user.is_staff = False
        self.admin_user.save()

        config.set("enable_team_leave", True)
        response = self.client.post(reverse("team-leave"))
        config.set("enable_team_leave", False)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_team_leave_as_owner_without_members(self):
        self.client.force_authenticate(user=self.user)

        config.set("enable_team_leave", True)
        response = self.client.post(reverse("team-leave"))
        config.set("enable_team_leave", False)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_team_leave_as_mortal(self) -> None:
        """Leaving as non-owner should leave the team without deletion."""

        # We create new regular user, and authenticate the request as a normal
        # member of the team (a non-owner).
        new_user = get_user_model()(
            username="team-test-2",
            email="team-test-2@example.org",
            is_visible=True,
        )
        new_user.team = self.team
        new_user.save()

        self.client.force_authenticate(user=new_user)

        config.set("enable_team_leave", True)
        response = self.client.post(reverse("team-leave"))
        config.set("enable_team_leave", False)
        self.assertEqual(response.status_code, HTTP_200_OK)


class CreateTeamTestCase(TeamSetupMixin, APITestCase):
    def test_create_team(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-create"), data={"name": "test-team", "password": "test"})
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_create_team_in_team(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("team-create"), data={"name": "test-team", "password": "test"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_team_not_authed(self):
        response = self.client.post(reverse("team-create"), data={"name": "test-team", "password": "test"})
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_create_duplicate_team(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-create"), data={"name": self.team.name, "password": "test"})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_disallows_create_team_with_differently_cased_but_same_name(self):
        """A differently-cased but otherwise same name should not be allowed creation."""

        self.client.force_authenticate(self.admin_user)
        payload = {"name": self.team.name.upper(), "password": "test"}
        response = self.client.post(reverse("team-create"), data=payload)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class JoinTeamTestCase(TeamSetupMixin, APITestCase):
    def test_join_team(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_join_team_incorrect_password(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "incorrect_pass"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_incorrect_name(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "incorrect-team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_join_team_full(self):
        user2 = get_user_model()(username="team-test2", email="team-test2@example.org", is_visible=True)
        user2.save()
        self.client.force_authenticate(self.admin_user)
        config.set("team_size", 1)
        self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.client.force_authenticate(user2)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_disabled(self):
        self.client.force_authenticate(self.admin_user)
        config.set("enable_team_join", False)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        config.set("enable_team_join", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_duplicate(self):
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_not_authed(self):
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_join_team_team_owner(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_malformed(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test"})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class TeamViewsetTestCase(TeamSetupMixin, APITestCase):
    def test_visible_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-list"))
        self.assertEqual(len(response.data["d"]["results"]), 1)

    def test_visible_not_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("team-list"))

        self.assertEqual(len(response.data["d"]["results"]), 0)

    def test_visible_detail_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_visible_detail_not_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.id}))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_view_password_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.id}))
        self.assertTrue("password" in response.data)

    def test_view_password_not_admin(self):
        self.admin_user.is_staff = False
        self.admin_user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.id}))
        self.assertFalse("password" in response.data)

    def test_view_team(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_patch_team(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(reverse("team-detail", kwargs={"pk": self.team.id}), data={"name": "test"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_patch_team_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.patch(reverse("team-detail", kwargs={"pk": self.team.id}), data={"name": "test"})
        self.assertEqual(response.status_code, HTTP_200_OK)
