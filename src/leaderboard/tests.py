"""Tests for the leaderboard app."""

from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase
from team.models import Team

from challenge.models import Category, Challenge, Score, Solve
from config import config
from leaderboard.views import CTFTimeListView, GraphView, TeamListView, UserListView


def populate():
    """Populate the database with some example data."""
    category = Category(name="test", display_order=0, contained_type="test", description="")
    category.save()
    challenge = Challenge(
        name="test3",
        category=category,
        description="a",
        challenge_type="basic",
        challenge_metadata={},
        flag_type="plaintext",
        flag_metadata={"flag": "ractf{a}"},
        author="aaa",
        score=1000,
        unlock_requirements="",
    )
    challenge.save()
    for i in range(15):
        user = get_user_model()(username=f"scorelist-test{i}", email=f"scorelist-test{i}@example.org", is_visible=True)
        user.save()
        team = Team(name=f"scorelist-test{i}", password=f"scorelist-test{i}", owner=user, is_visible=True)
        team.points = i * 100
        team.leaderboard_points = i * 100
        team.save()
        user.team = team
        user.points = i * 100
        user.leaderboard_points = i * 100
        user.save()
        Score(team=team, user=user, reason="test", points=i * 100).save()
        if i % 2 == 0:
            Solve(team=team, solved_by=user, challenge=challenge).save()


class ScoreListTestCase(APITestCase):
    """Tests for the scorelist endpoint."""

    def setUp(self):
        """Remove ratelimits from the graph view and create a user."""
        GraphView.throttle_scope = ""
        user = get_user_model()(username="scorelist-test", email="scorelist-test@example.org")
        user.save()
        self.user = user

    def test_unauthed_access(self):
        """Test an unauthenticated user can access the leaderboard."""
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed_access(self):
        """Test an authenticated user can access the leaderboard."""
        self.client.force_authenticate(self.user)
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        """Test an unauthenticated user cannot access the leaderboard when its disabled."""
        config.set("enable_caching", False)
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_scoreboard", True)
        config.set("enable_caching", True)
        self.assertEqual(response.data["d"], {})

    def test_format(self):
        """Test the leaderboard is formatted correctly."""
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertTrue("user" in response.data["d"])
        self.assertTrue("team" in response.data["d"])

    def test_list_size(self):
        """Test the leaderboard contains the right amount of users."""
        config.set("enable_caching", False)
        populate()
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(len(response.data["d"]["user"]), 10)
        self.assertEqual(len(response.data["d"]["team"]), 10)

    def test_list_sorting(self):
        """Test the leaderboard is ordered correctly."""
        config.set("enable_caching", False)
        populate()
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(response.data["d"]["user"][0]["points"], 1400)
        self.assertEqual(response.data["d"]["team"][0]["points"], 1400)

    def test_user_only(self):
        """Test the leaderboard only displays users when teams are disabled."""
        populate()
        config.set("enable_teams", False)
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_teams", True)
        config.set("enable_caching", True)
        self.assertEqual(len(response.data["d"]["user"]), 10)
        self.assertEqual(response.data["d"]["user"][0]["points"], 1400)
        self.assertNotIn("team", response.data["d"].keys())

    def test_caching(self):
        """Test the leaderboard is cached correctly."""
        config.set("enable_caching", True)
        uncached_response = self.client.get(reverse("leaderboard-graph"))
        cached_response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", False)
        self.assertEqual(uncached_response.data, cached_response.data)


class UserListTestCase(APITestCase):
    """Tests for the user scoreboard."""

    def setUp(self):
        """Remove the rate limit for the view."""
        user = get_user_model()(username="userlist-test", email="userlist-test@example.org")
        user.save()
        self.user = user
        UserListView.throttle_scope = None

    def test_unauthed(self):
        """Test an unauthenticated user can access the view."""
        response = self.client.get(reverse("leaderboard-user"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        """Test an authenticated user can access the view."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-user"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        """Test the scoreboard cannot be accessed when enable_scoreboard is False."""
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-user"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data["d"], {})

    def test_length(self):
        """Test the length of the scoreboard is correct."""
        populate()
        response = self.client.get(reverse("leaderboard-user"))
        self.assertEqual(len(response.data["d"]["results"]), 15)

    def test_order(self):
        """Test the order of the scoreboard is correct."""
        populate()
        response = self.client.get(reverse("leaderboard-user"))
        points = [x["leaderboard_points"] for x in response.data["d"]["results"]]
        self.assertEqual(points, sorted(points, reverse=True))


class TeamListTestCase(APITestCase):
    """Tests for the team scoreboard."""

    def setUp(self):
        """Remove the rate limit for the view."""
        user = get_user_model()(username="userlist-test", email="userlist-test@example.org")
        user.save()
        self.user = user
        TeamListView.throttle_scope = None

    def test_unauthed(self):
        """Test an unauthenticated user can access the view."""
        response = self.client.get(reverse("leaderboard-team"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        """Test an authenticated user can access the view."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-team"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        """Test the scoreboard cannot be accessed when enable_scoreboard is False."""
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-team"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data["d"], {})

    def test_length(self):
        """Test the length of the scoreboard is correct."""
        populate()
        response = self.client.get(reverse("leaderboard-team"))
        self.assertEqual(len(response.data["d"]["results"]), 15)

    def test_order(self):
        """Test the order of the scoreboard is correct."""
        populate()
        response = self.client.get(reverse("leaderboard-team"))
        points = [x["leaderboard_points"] for x in response.data["d"]["results"]]
        self.assertEqual(points, sorted(points, reverse=True))


class CTFTimeListTestCase(APITestCase):
    """Test the CTFTime scoreboard integration."""

    def setUp(self):
        """Remove the rate limit for the view."""
        user = get_user_model()(username="userlist-test", email="userlist-test@example.org")
        user.save()
        self.user = user
        CTFTimeListView.throttle_scope = None

    def test_unauthed(self):
        """Test an unauthenticated user can access the view."""
        response = self.client.get(reverse("leaderboard-ctftime"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        """Test an authenticated user can access the view."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-ctftime"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        """Test the scoreboard cannot be accessed when enable_scoreboard is False."""
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-ctftime"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data, {})

    def test_disabled_ctftime(self):
        """Test the scoreboard cannot be accessed when enable_ctftime is False."""
        config.set("enable_ctftime", False)
        response = self.client.get(reverse("leaderboard-ctftime"))
        config.set("enable_ctftime", True)
        self.assertEqual(response.data, {})

    def test_length(self):
        """Test the length of the scoreboard is correct."""
        populate()
        response = self.client.get(reverse("leaderboard-ctftime"))
        self.assertEqual(len(response.data["standings"]), 15)

    def test_order(self):
        """Test the order of the scoreboard is correct."""
        populate()
        response = self.client.get(reverse("leaderboard-ctftime"))
        points = [x["score"] for x in response.data["standings"]]
        self.assertEqual(points, sorted(points, reverse=True))


class MatrixTestCase(APITestCase):
    """Test the matrix scoreboard."""

    def setUp(self):
        """Remove the rate limit for the view."""
        user = get_user_model()(username="matrix-test", email="matrix-test@example.org")
        user.save()
        self.user = user
        TeamListView.throttle_scope = None
        populate()

    def test_authenticated(self):
        """Test an authenticated user can access the view."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_unauthenticated(self):
        """Test an unauthenticated user can access the view."""
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_length(self):
        """Test the length of the scoreboard is correct."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(len(response.data["d"]["results"]), 15)

    def test_solves_present(self):
        """Test solves are displayed."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(len(response.data["d"]["results"][0]["solve_ids"]), 1)

    def test_solves_not_present(self):
        """Test the only challenges included are ones the user has solved."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(len(response.data["d"]["results"][1]["solve_ids"]), 0)

    def test_order(self):
        """Test the order of the scoreboard is correct."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        points = [x["leaderboard_points"] for x in response.data["d"]["results"]]
        self.assertEqual(points, sorted(points, reverse=True))

    def test_disabled_scoreboard(self):
        """Test the scoreboard cannot be accessed when enable_scoreboard is False."""
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data["d"], {})
