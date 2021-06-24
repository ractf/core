"""Unit tests for the teams app."""
import random

from django.contrib.auth import get_user_model
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
from team.models import Team

from challenge.models import Category, Challenge, Score, Solve
from config import config


class TeamSetupMixin:
    """Mixin to add a setup method to team tests."""

    def setUp(self):
        """Create some users and teams for testing."""
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
    """Tests for the team-self endpoint."""

    def test_team_self(self):
        """Test an authenticated user with a team can view the endpoint."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_team_password(self):
        """Test the user can read the team password."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["password"], "abc")

    def test_no_team(self):
        """Test the endpoint 404s if the user has no team."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_not_authed(self):
        """Test the endpoint cannot be accessed by unauthorized users."""
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_update(self):
        """Test the owner of a team can change the team name."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(reverse("team-self"), data={"name": "name-change"})
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["name"], "name-change")

    def test_update_not_owner(self):
        """Test a user who isnt the owner of their team cannot change the team name."""
        self.admin_user.team = self.team
        self.admin_user.is_staff = False
        self.admin_user.save()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(reverse("team-self"), data={"name": "name-change"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_team_leave_disabled(self):
        """Leaving a team should be blocked if enable_team_leave is False."""
        self.client.force_authenticate(user=self.user)
        config.set("enable_team_leave", False)
        response = self.client.post(reverse("team-leave"))
        config.set("enable_team_leave", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_team_leave_challenge_solved(self):
        """Leaving a team should be blocked if the team has solved a challenge."""
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
        """Leaving as owner should be blocked if the team has other members."""
        self.client.force_authenticate(user=self.user)

        self.admin_user.team = self.team
        self.admin_user.is_staff = False
        self.admin_user.save()

        config.set("enable_team_leave", True)
        response = self.client.post(reverse("team-leave"))
        config.set("enable_team_leave", False)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_team_leave_as_owner_without_members(self):
        """Leaving as owner with noone else in the team should delete the team."""
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
    """Tests for creating a team."""

    def test_create_team(self):
        """A user without a team should be able to create a team."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-create"), data={"name": "test-team", "password": "test"})
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_create_team_in_team(self):
        """A user with a team should not be able to create a team."""
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("team-create"), data={"name": "test-team", "password": "test"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_team_not_authed(self):
        """An unauthenticated user should not be able to create a team."""
        response = self.client.post(reverse("team-create"), data={"name": "test-team", "password": "test"})
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_create_duplicate_team(self):
        """A team should not be able to be created with a name that already exists."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-create"), data={"name": "team-test", "password": "test"})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class JoinTeamTestCase(TeamSetupMixin, APITestCase):
    """Tests for joining a team."""

    def test_join_team(self):
        """A user without a team should be able to join a team with the correct name and password."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_join_team_incorrect_password(self):
        """A user without a team should not be able to join a team with the correct name and incorrect password."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "incorrect_pass"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_incorrect_name(self):
        """A user without a team should not be able to join a team with the incorrect name and correct password."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "incorrect-team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_join_team_full(self):
        """A user without a team should not be able to join a full team."""
        user2 = get_user_model()(username="team-test2", email="team-test2@example.org", is_visible=True)
        user2.save()
        self.client.force_authenticate(self.admin_user)
        config.set("team_size", 1)
        self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.client.force_authenticate(user2)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_disabled(self):
        """A user without a team should not be able to join a team when team join is disabled."""
        self.client.force_authenticate(self.admin_user)
        config.set("enable_team_join", False)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        config.set("enable_team_join", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_duplicate(self):
        """A user should not be able to join a team twice."""
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_not_authed(self):
        """An unauthenticated user should not be able to join a team."""
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_join_team_team_owner(self):
        """A user should not be able to join a team they own."""
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test", "password": "abc"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_malformed(self):
        """A malformed team join request should be rejected."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-join"), data={"name": "team-test"})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)


class TeamViewsetTestCase(TeamSetupMixin, APITestCase):
    """Tests for TeamViewset."""

    def test_visible_admin(self):
        """All teams should be visible to admins."""
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-list"))
        self.assertEqual(len(response.data["d"]["results"]), 1)

    def test_visible_not_admin(self):
        """Only teams where is_visible=True should be visible to admins."""
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("team-list"))

        self.assertEqual(len(response.data["d"]["results"]), 0)

    def test_visible_detail_admin(self):
        """An admin should be able to view the details of a team where is_visible=False."""
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.pk}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_visible_detail_not_admin(self):
        """A non admin should not be able to view the details of a team where is_visible=False."""
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.pk}))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_view_password_admin(self):
        """An admin should be able to view the password of any team."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.pk}))
        self.assertTrue("password" in response.data)

    def test_view_password_not_admin(self):
        """A non admin should not be able to view the password of any team."""
        self.admin_user.is_staff = False
        self.admin_user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.pk}))
        self.assertFalse("password" in response.data)

    def test_view_team(self):
        """A non admin should be able to view the details of a team where is_visible=True."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("team-detail", kwargs={"pk": self.team.pk}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_patch_team(self):
        """A normal user modifying a team should be rejected."""
        self.client.force_authenticate(self.user)
        response = self.client.patch(reverse("team-detail", kwargs={"pk": self.team.pk}), data={"name": "test"})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_patch_team_admin(self):
        """An admin should be able to modify other teams."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.patch(reverse("team-detail", kwargs={"pk": self.team.pk}), data={"name": "test"})
        self.assertEqual(response.status_code, HTTP_200_OK)


class RecalculateTeamViewTestCase(APITestCase):
    """Tests for recalculating the score of a team."""

    def setUp(self):
        """Create users and teams for testing."""
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
        """An unauthenticated user should not be able to access this endpoint."""
        response = self.client.post(reverse("team-recalculate-score", kwargs={"pk": self.team.pk}))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authed(self):
        """An authenticated admin user should be able to access this endpoint."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-recalculate-score", kwargs={"pk": self.team.pk}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed_not_admin(self):
        """An authenticated non-admin user should not be able to access this endpoint."""
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("team-recalculate-score", kwargs={"pk": self.team.pk}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_recalculate(self):
        """The recalculation should be equal to the sum of all the teams scores."""
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("team-recalculate-score", kwargs={"pk": self.team.pk}))
        self.assertEqual(Team.objects.get(id=self.team.pk).points, total + 100)

    def test_recalculate_leaderboard(self):
        """Score objects where leaderboard=False should not be included in leaderboard_points."""
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("team-recalculate-score", kwargs={"pk": self.team.pk}))
        self.assertEqual(Team.objects.get(id=self.team.pk).leaderboard_points, total)


class RecalculateAllViewTestCase(APITestCase):
    """Tests for recalculating the scores of every team."""

    def setUp(self):
        """Create users and teams for testing."""
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
        """An unauthenticated user should not be able to access this endpoint."""
        response = self.client.post(reverse("team-recalculate-all-scores"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authed(self):
        """An authenticated admin user should be able to access this endpoint."""
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("team-recalculate-all-scores"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed_not_admin(self):
        """An authenticated non-admin user should not be able to access this endpoint."""
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("team-recalculate-all-scores"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_recalculate(self):
        """The recalculation should be equal to the sum of all the teams scores."""
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("team-recalculate-all-scores"))
        self.assertEqual(Team.objects.get(id=self.team.pk).points, total + 100)
        self.assertEqual(get_user_model().objects.get(id=self.user.pk).points, total + 100)

    def test_recalculate_leaderboard(self):
        """Score objects where leaderboard=False should not be included in leaderboard_points."""
        total = 0
        for i in range(15):
            points = random.randint(0, 100)
            total += points
            Score(team=self.team, user=self.user, reason="test", points=points).save()
        Score(team=self.team, user=self.user, reason="test", points=100, leaderboard=False).save()
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse("team-recalculate-all-scores"))
        self.assertEqual(Team.objects.get(id=self.team.pk).leaderboard_points, total)
        self.assertEqual(get_user_model().objects.get(id=self.user.pk).leaderboard_points, total)
