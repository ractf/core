"""Unit tests for the challenge api endpoints."""

from challenge.models import Solve
from challenge.tests.mixins import ChallengeSetupMixin
import time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from rest_framework.test import APITestCase

from config import config
from hint.models import HintUse


class ChallengeTestCase(ChallengeSetupMixin, APITestCase):
    """Tests for the challenge api routes."""

    def solve_challenge(self):
        """Solve a challenge."""
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        return self.client.post(reverse("submit-flag"), data)

    def test_challenge_solve(self):
        """Test that a challenge can be solved."""
        response = self.solve_challenge()
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["d"]["correct"], True)

    def test_challenge_solve_incorrect_flag(self):
        """Test that a challenge cant be solved with an incorrect flag."""
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{b}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["d"]["correct"], False)

    def test_challenge_double_solve(self):
        """Test that a challenge cant be solved twice."""
        self.solve_challenge()
        self.client.force_authenticate(user=self.user2)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_solve_challenge_not_unlocked(self):
        """Test that a locked challenge cant be solved."""
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge3.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_solve_challenge_attempt_limit_reached(self):
        """Test that a challenge cant be solved once its attempt limit is reached."""
        self.client.force_authenticate(user=self.user)
        self.challenge2.challenge_metadata = {"attempt_limit": -1}
        self.challenge2.save()
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.challenge2.challenge_metadata = {}
        self.challenge2.save()
        self.assertEqual(response.data["m"], "attempt_limit_reached")

    def test_solve_challenge_attempt_limit_not_reached(self):
        """Test that a challenge with an attempt limit can be solved when the attempt limit isnt reached."""
        self.client.force_authenticate(user=self.user)
        self.challenge2.challenge_metadata = {"attempt_limit": 5000}
        self.challenge2.save()
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.challenge2.challenge_metadata = {}
        self.challenge2.save()
        self.assertNotEqual(response.data["m"], "attempt_limit_reached")

    def test_solve_challenge_with_explanation(self):
        """Test that an explanation is sent when a challenge is solved."""
        self.client.force_authenticate(user=self.user)
        self.challenge2.post_score_explanation = "test"
        self.challenge2.save()
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertTrue("explanation" in response.data["d"])

    def test_challenge_unlocks(self):
        """Test that a challenge can be unlocked."""
        self.solve_challenge()
        self.challenge1.unlock_requirements = str(self.challenge2.pk)
        self.assertTrue(self.challenge1.is_unlocked_by(get_user_model().objects.get(id=self.user.pk)))

    def test_challenge_unlocks_no_team(self):
        """Test that challenges are locked until you have a team."""
        user4 = get_user_model()(username="challenge-test-4", email="challenge-test-4@example.org")
        user4.save()
        self.assertFalse(self.challenge1.is_unlocked_by(user4))

    def test_challenge_unlocks_locked(self):
        """That that challenges are correctly locked."""
        self.assertFalse(self.challenge1.is_unlocked_by(self.user))

    def test_hint_scoring(self):
        """Test hint penalties are correctly applied."""
        HintUse(hint=self.hint3, team=self.team, user=self.user, challenge=self.challenge2).save()
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["points"], 900)

    def test_solve_first_blood(self):
        """Test first blood is correctly applied to solves."""
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["first_blood"], True)

    def test_solve_solved_by_name(self):
        """Test the solved_by_name is supplied correctly."""
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["solved_by_name"], "challenge-test")

    def test_solve_team_name(self):
        """Test the team name is supplied correctly."""
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["team_name"], "team")

    def test_normal_scoring(self):
        """Test solves are scored correctly."""
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["points"], 1000)

    def test_is_solved_by(self):
        """Test challenges correctly report when they are solved."""
        self.solve_challenge()
        self.assertTrue(self.challenge2.is_solved_by(user=self.user))

    def test_is_not_solved(self):
        """Test challenges correctly report being unsolved."""
        self.assertFalse(self.challenge1.is_solved_by(user=self.user))

    def test_submission_disabled(self):
        """Test flags cannot be submitted when enable_flag_submission is false."""
        config.set("enable_flag_submission", False)
        response = self.solve_challenge()
        config.set("enable_flag_submission", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_submission_malformed(self):
        """Test a malformed flag submission is rejected."""
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{a}",
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_challenge_score_same_team(self):
        """Test a challenge cannot be solved by 2 people on the same team."""
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        self.client.post(reverse("submit-flag"), data)
        self.client.force_authenticate(user=self.user2)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_challenge_score_not_first_blood(self):
        """Test a solve is not incorrectly marked first blood."""
        self.solve_challenge()
        self.client.force_authenticate(user=self.user3)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(Solve.objects.get(team=self.team2, challenge=self.challenge2).first_blood)

    def test_challenge_solved_unauthed(self):
        """Test is_solved returns False early for anonymous users."""
        self.assertFalse(self.challenge2.is_solved_by(AnonymousUser()))

    def test_challenge_unlocked_unauthed(self):
        """Test is_unlocked returns False early for anonymous users."""
        self.assertFalse(self.challenge2.is_unlocked_by(AnonymousUser()))

    def test_challenge_solved_no_team(self):
        """Test is_solved returns False early for users with no team."""
        user4 = get_user_model()(username="challenge-test-4", email="challenge-test-4@example.org")
        user4.save()
        self.assertFalse(self.challenge2.is_solved_by(user4))

    def test_challenge_solve_non_tiebreak(self):
        """"Test solving a challenge that is not a tiebreaker does not update last_score."""
        self.challenge2.tiebreaker = False
        self.challenge2.save()
        last_score_before = self.user.last_score
        self.solve_challenge()
        self.assertEqual(last_score_before, self.user.last_score)


class CategoryViewsetTestCase(ChallengeSetupMixin, APITestCase):
    """Tests for the /challenge/categories/ endpoints."""

    def test_category_list_unauthenticated_permission(self):
        """Test unauthenticated users cannot list categories."""
        response = self.client.get(reverse("categories-list"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_category_list_authenticated_permission(self):
        """Test authenticated users can list categories."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_category_list_unauthenticated_content(self):
        """Test unauthenticated users do not get any content from the category list."""
        response = self.client.get(reverse("categories-list"))
        self.assertFalse(response.data["s"])
        self.assertEqual(response.data["m"], "not_authenticated")
        self.assertEqual(response.data["d"], "")

    def test_category_list_authenticated_content(self):
        """Test authenticated users do get content from the category list."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertEqual(len(response.data["d"]), 1)
        self.assertEqual(len(response.data["d"][0]["challenges"]), 3)

    def test_category_list_challenge_redacting(self):
        """Test the category list is correctly redacted."""
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        config.set("enable_caching", False)
        self.assertFalse("description" in self.find_challenge_entry(self.challenge1, data=response.data))

    def test_category_list_challenge_redacting_admin(self):
        """Test the category list is not redacted for admins."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        config.set("enable_caching", False)
        response = self.client.get(reverse("categories-list"))
        self.assertTrue("description" in self.find_challenge_entry(self.challenge3, data=response.data))

    def test_category_list_challenge_redacting_admin_denied(self):
        """Test the category list is redacted for admins that are being denied admin permissions."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        config.set("enable_caching", False)
        config.set("enable_force_admin_2fa", True)
        response = self.client.get(reverse("categories-list"))
        config.set("enable_force_admin_2fa", False)
        self.assertEqual(response.data["d"], [])

    def test_category_list_challenge_unlocked_admin(self):
        """Test the category list correctly sets unlocked for admins."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertFalse(self.find_challenge_entry(self.challenge1, data=response.data).get("unlocked"))

    def test_category_create(self):
        """Test categories can be created."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("categories-list"),
            data={
                "name": "test-category-2",
                "contained_type": "test",
                "description": "test",
            },
        )
        self.assertTrue(response.status_code, HTTP_200_OK)

    def test_category_create_unauthorized(self):
        """Test unauthorized users cannot create categories."""
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("categories-list"),
            data={
                "name": "test-category-2",
                "contained_type": "test",
                "description": "test",
            },
        )
        self.assertTrue(response.status_code, HTTP_403_FORBIDDEN)

    def test_category_list_content_cached(self):
        """Test the category list is correctly cached."""
        self.client.force_authenticate(self.user)
        config.set("enable_caching", True)
        uncached_response = self.client.get(reverse("categories-list"))
        cached_response = self.client.get(reverse("categories-list"))
        config.set("enable_caching", False)
        self.assertEqual(uncached_response.data, cached_response.data)

    def test_category_list_content_preevent_cached(self):
        """Test the preevent cache is served to users."""
        self.client.force_authenticate(self.user)
        config.set("enable_preevent_cache", True)
        config.set("start_time", time.time() - 5)
        caches["default"].set("preevent_cache", {"key": "value"})
        cached_response = self.client.get(reverse("categories-list"))
        config.set("enable_preevent_cache", False)
        self.assertEqual(cached_response.data["d"], {"key": "value"})

    def test_category_list_content_preevent_cached_admin(self):
        """Test the preevent cache is not served to admins."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        config.set("enable_preevent_cache", True)
        caches["default"].set("preevent_cache", {"key": "value"})
        cached_response = self.client.get(reverse("categories-list"))
        config.set("enable_preevent_cache", False)
        self.assertNotEqual(cached_response.data["d"], {"key": "value"})


class ChallengeViewsetTestCase(ChallengeSetupMixin, APITestCase):
    """Tests for the challenge viewset api endpoints."""

    def test_challenge_list_unauthenticated_permission(self):
        """Test the endpoint cannot be accessed by unauthenticated users."""
        response = self.client.get(reverse("challenges-list"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_challenge_list_authenticated_permission(self):
        """Test the list can be viewed by authenticated users."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_challenge_list_unauthenticated_content(self):
        """Test unauthenticated users get no content from the endpoint."""
        response = self.client.get(reverse("challenges-list"))
        self.assertFalse(response.data["s"])
        self.assertEqual(response.data["m"], "not_authenticated")
        self.assertEqual(response.data["d"], "")

    def test_challenge_list_authenticated_content(self):
        """Test the correct amount of challenges are listed."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertEqual(len(response.data), 3)

    def test_challenge_list_challenge_redacting(self):
        """Test challenges are correctly redacted."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertFalse("description" in self.find_challenge_entry(self.challenge3, data=response.data))

    def test_challenge_list_challenge_redacting_admin(self):
        """Test challenges are not redacted for admins."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertTrue("description" in response.data[0])

    def test_challenge_list_challenge_unlocked_admin(self):
        """Test unlocked is correctly set for admins."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertFalse(self.find_challenge_entry(self.challenge1, data=response.data)["unlocked"])

    def test_single_challenge_redacting(self):
        """Test single challenges are correctly redacted."""
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertFalse("description" in response.data)

    def test_single_challenge_admin_redacting(self):
        """Test single challenges are not redacted for admins."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertTrue("description" in response.data)

    def test_admin_unlocking(self):
        """Test unlocked is correctly set on the detail view for admins."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertFalse(response.data["unlocked"])

    def test_user_post_detail(self):
        """Test non staff users cannot post to the challenge detail endpoint."""
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_user_post_list(self):
        """Test non staff users cannot post to the challenge list endpoint."""
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("challenges-list"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_challenge(self):
        """Test challenges can be created."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("challenges-list"),
            data={
                "name": "test4",
                "category": self.category.pk,
                "description": "abc",
                "challenge_type": "test",
                "challenge_metadata": {},
                "flag_type": "plaintext",
                "author": "dave",
                "score": 1000,
                "unlock_requirements": "",
                "flag_metadata": {},
                "tags": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_create_challenge_unauthorized(self):
        """Test unauthorized users cannot create challenges."""
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("challenges-list"),
            data={
                "name": "test4",
                "category": self.category.pk,
                "description": "abc",
                "challenge_type": "test",
                "challenge_metadata": {},
                "flag_type": "plaintext",
                "author": "dave",
                "score": 1000,
                "unlock_requirements": "a",
                "flag_metadata": {},
            },
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_challenge_metadata_saves(self):
        """Test challenge_metadata is saved."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        metadata = {
            "a": "b",
            "c": "d",
        }
        self.client.patch(
            reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}),
            data={
                "challenge_metadata": metadata,
            },
            format="json",
        )
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertEquals(response.data["challenge_metadata"], metadata)


class FlagCheckViewTestCase(ChallengeSetupMixin, APITestCase):
    """Tests for the flag check endpoint."""

    def test_disable_flag_submission(self):
        """Test flags cannot be checked with flag submission disabled."""
        self.client.force_authenticate(self.user)
        config.set("enable_flag_submission", False)
        response = self.client.post(reverse("check-flag"))
        config.set("enable_flag_submission", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_bad_request(self):
        """Test malformed requests are rejected."""
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("check-flag"))
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_havent_solved_challenge(self):
        """Test the endpoint rejects challenges that the user has not solved."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("check-flag"),
            data={
                "challenge": self.challenge1.pk,
                "flag": "a",
            },
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_incorrect_flag(self):
        """Test the incorrect flag is rejected."""
        self.client.force_authenticate(self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        self.client.post(reverse("submit-flag"), data)
        response = self.client.post(
            reverse("check-flag"),
            data={
                "challenge": self.challenge2.pk,
                "flag": "a",
            },
        )
        self.assertEqual(response.data["m"], "incorrect_flag")

    def test_correct_flag(self):
        """Test the correct flag is accepted."""
        self.client.force_authenticate(self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        self.client.post(reverse("submit-flag"), data)
        response = self.client.post(reverse("check-flag"), data)
        self.assertEqual(response.data["m"], "correct_flag")

    def test_post_score_explanation(self):
        """Test the post score explanation is correctly included."""
        self.client.force_authenticate(self.user)
        self.challenge2.post_score_explanation = "test"
        self.challenge2.save()
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        self.client.post(reverse("submit-flag"), data)
        response = self.client.post(reverse("check-flag"), data)
        self.assertTrue("explanation" in response.data["d"])
