from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from challenge.models import Category, Challenge, Score, Solve
from config import config
from leaderboard.views import CTFTimeListView, GraphView, TeamListView, UserListView
from team.models import Team


def populate():
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
    def setUp(self):
        GraphView.throttle_scope = ""
        user = get_user_model()(username="scorelist-test", email="scorelist-test@example.org")
        user.save()
        self.user = user

    def test_unauthed_access(self):
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed_access(self):
        self.client.force_authenticate(self.user)
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        config.set("enable_caching", False)
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_scoreboard", True)
        config.set("enable_caching", True)
        self.assertEqual(response.data["d"], {})

    def test_format(self):
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertTrue("user" in response.data["d"])
        self.assertTrue("team" in response.data["d"])

    def test_list_size(self):
        config.set("enable_caching", False)
        populate()
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(len(response.data["d"]["user"]), 10)
        self.assertEqual(len(response.data["d"]["team"]), 10)

    def test_list_sorting(self):
        config.set("enable_caching", False)
        populate()
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_caching", True)
        self.assertEqual(response.data["d"]["user"][0]["points"], 1400)
        self.assertEqual(response.data["d"]["team"][0]["points"], 1400)

    def test_user_only(self):
        populate()
        config.set("enable_teams", False)
        config.set("enable_caching", False)
        response = self.client.get(reverse("leaderboard-graph"))
        config.set("enable_teams", True)
        config.set("enable_caching", True)
        self.assertEqual(len(response.data["d"]["user"]), 10)
        self.assertEqual(response.data["d"]["user"][0]["points"], 1400)
        self.assertNotIn("team", response.data["d"].keys())


class UserListTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="userlist-test", email="userlist-test@example.org")
        user.save()
        self.user = user
        UserListView.throttle_scope = None

    def test_unauthed(self):
        response = self.client.get(reverse("leaderboard-user"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-user"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-user"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data["d"], {})

    def test_length(self):
        populate()
        response = self.client.get(reverse("leaderboard-user"))
        self.assertEqual(len(response.data["d"]["results"]), 15)

    def test_order(self):
        populate()
        response = self.client.get(reverse("leaderboard-user"))
        points = [x["leaderboard_points"] for x in response.data["d"]["results"]]
        self.assertEqual(points, sorted(points, reverse=True))


class TeamListTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="userlist-test", email="userlist-test@example.org")
        user.save()
        self.user = user
        TeamListView.throttle_scope = None

    def test_unauthed(self):
        response = self.client.get(reverse("leaderboard-team"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-team"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-team"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data["d"], {})

    def test_length(self):
        populate()
        response = self.client.get(reverse("leaderboard-team"))
        self.assertEqual(len(response.data["d"]["results"]), 15)

    def test_order(self):
        populate()
        response = self.client.get(reverse("leaderboard-team"))
        points = [x["leaderboard_points"] for x in response.data["d"]["results"]]
        self.assertEqual(points, sorted(points, reverse=True))


class CTFTimeListTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="userlist-test", email="userlist-test@example.org")
        user.save()
        self.user = user
        CTFTimeListView.throttle_scope = None

    def test_unauthed(self):
        response = self.client.get(reverse("leaderboard-ctftime"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_authed(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-ctftime"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_disabled_access(self):
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-ctftime"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data, {})

    def test_disabled_ctftime(self):
        config.set("enable_ctftime", False)
        response = self.client.get(reverse("leaderboard-ctftime"))
        config.set("enable_ctftime", True)
        self.assertEqual(response.data, {})

    def test_length(self):
        populate()
        response = self.client.get(reverse("leaderboard-ctftime"))
        self.assertEqual(len(response.data["standings"]), 15)

    def test_order(self):
        populate()
        response = self.client.get(reverse("leaderboard-ctftime"))
        points = [x["score"] for x in response.data["standings"]]
        self.assertEqual(points, sorted(points, reverse=True))


class MatrixTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="matrix-test", email="matrix-test@example.org")
        user.save()
        self.user = user
        TeamListView.throttle_scope = None
        populate()

    def test_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_unauthenticated(self):
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_length(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(len(response.data["d"]["results"]), 15)

    def test_solves_present(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(len(response.data["d"]["results"][0]["solve_ids"]), 1)

    def test_solves_not_present(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        self.assertEqual(len(response.data["d"]["results"][1]["solve_ids"]), 0)

    def test_order(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        points = [x["leaderboard_points"] for x in response.data["d"]["results"]]
        self.assertEqual(points, sorted(points, reverse=True))

    def test_disabled_scoreboard(self):
        config.set("enable_scoreboard", False)
        response = self.client.get(reverse("leaderboard-matrix-list"))
        config.set("enable_scoreboard", True)
        self.assertEqual(response.data["d"], {})
