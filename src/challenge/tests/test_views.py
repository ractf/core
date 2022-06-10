import time

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_204_NO_CONTENT,
)
from rest_framework.test import APITestCase

from challenge.models import Solve, ChallengeVote, ChallengeFeedback, Tag
from challenge.tests.mixins import ChallengeSetupMixin
from config import config
from hint.models import HintUse
from member.models import Member


class ChallengeTestCase(ChallengeSetupMixin, APITestCase):

    def test_challenge_solve(self):
        response = self.solve_challenge()
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["d"]["correct"], True)

    def test_challenge_solve_incorrect_flag(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{b}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["d"]["correct"], False)

    def test_challenge_double_solve(self):
        self.solve_challenge()
        self.client.force_authenticate(user=self.user2)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_solve_challenge_not_unlocked(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge3.pk,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_solve_challenge_attempt_limit_reached(self):
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
        self.solve_challenge()
        self.challenge1.unlock_requirements = str(self.challenge2.pk)
        self.assertTrue(self.challenge1.is_unlocked(Member.objects.get(id=self.user.pk)))

    def test_challenge_unlocks_no_team(self):
        user4 = Member(username="challenge-test-4", email="challenge-test-4@example.org")
        user4.save()
        self.assertFalse(self.challenge1.is_unlocked(user4))

    def test_challenge_unlocks_locked(self):
        self.assertFalse(self.challenge1.is_unlocked(self.user))

    def test_hint_scoring(self):
        HintUse(hint=self.hint3, team=self.team, user=self.user, challenge=self.challenge2).save()
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["points"], 900)

    def test_solve_first_blood(self):
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["first_blood"], True)

    def test_solve_solved_by_name(self):
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["solved_by_name"], "challenge-test")

    def test_solve_team_name(self):
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["team_name"], "team")

    def test_normal_scoring(self):
        self.solve_challenge()
        response = self.client.get(reverse("team-self"))
        self.assertEqual(response.data["solves"][0]["points"], 1000)

    def test_is_solved(self):
        self.solve_challenge()
        self.assertTrue(self.challenge2.is_solved(user=self.user))

    def test_is_not_solved(self):
        self.assertFalse(self.challenge1.is_solved(user=self.user))

    def test_submission_disabled(self):
        config.set("enable_flag_submission", False)
        response = self.solve_challenge()
        config.set("enable_flag_submission", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_submission_malformed(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{a}",
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_challenge_score_same_team(self):
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
        self.assertFalse(self.challenge2.is_solved(AnonymousUser()))

    def test_challenge_unlocked_unauthed(self):
        self.assertFalse(self.challenge2.is_unlocked(AnonymousUser()))

    def test_challenge_solved_no_team(self):
        user4 = Member(username="challenge-test-4", email="challenge-test-4@example.org")
        user4.save()
        self.assertFalse(self.challenge2.is_solved(user4))

    def test_challenge_solve_non_tiebreak(self):
        self.challenge2.tiebreaker = False
        self.challenge2.save()
        last_score_before = self.user.last_score
        self.solve_challenge()
        self.assertEqual(last_score_before, self.user.last_score)

    def test_challenge_solve_decay(self):
        self.challenge2.points_type = "decay"
        self.challenge2.flag_metadata["decay_constant"] = 0.5
        self.challenge2.flag_metadata["min_points"] = 50
        self.challenge2.save()

        self.client.force_authenticate(self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        self.client.post(reverse("submit-flag"), data)

        self.user.refresh_from_db()
        points = self.user.points

        self.client.force_authenticate(self.user3)
        self.client.post(reverse("submit-flag"), data).json()

        self.user.refresh_from_db()
        self.assertLess(self.user.points, points)

    def test_challenge_solve_decay_current_score(self):
        self.challenge2.points_type = "decay"
        self.challenge2.flag_metadata["decay_constant"] = 0.5
        self.challenge2.flag_metadata["min_points"] = 50
        self.challenge2.save()

        self.client.force_authenticate(self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.pk,
        }
        self.client.post(reverse("submit-flag"), data)

        self.client.force_authenticate(self.user3)
        self.client.post(reverse("submit-flag"), data).json()

        self.challenge2.refresh_from_db()
        self.assertLess(self.challenge2.current_score, self.challenge2.score)


class CategoryViewsetTestCase(ChallengeSetupMixin, APITestCase):
    def test_category_list_unauthenticated_permission(self):
        response = self.client.get(reverse("categories-list"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_category_list_authenticated_permission(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_category_list_unauthenticated_content(self):
        response = self.client.get(reverse("categories-list"))
        self.assertFalse(response.data["s"])
        self.assertEqual(response.data["m"], "not_authenticated")
        self.assertEqual(response.data["d"], "")

    def test_category_list_authenticated_content(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertEqual(len(response.data["d"]), 1)
        self.assertEqual(len(response.data["d"][0]["challenges"]), 3)

    def test_category_list_challenge_redacting(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        config.set("enable_caching", False)
        self.assertFalse("description" in self.find_challenge_entry(self.challenge1, data=response.data))

    def test_category_list_challenge_redacting_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        config.set("enable_caching", False)
        response = self.client.get(reverse("categories-list"))
        self.assertTrue("description" in self.find_challenge_entry(self.challenge3, data=response.data))

    def test_category_list_challenge_redacting_admin_denied(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        config.set("enable_caching", False)
        config.set("enable_force_admin_2fa", True)
        response = self.client.get(reverse("categories-list"))
        config.set("enable_force_admin_2fa", False)
        self.assertEqual(response.data["d"], [])

    def test_category_list_challenge_unlocked_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertFalse(self.find_challenge_entry(self.challenge1, data=response.data).get("unlocked"))

    def test_category_create(self):
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
        self.client.force_authenticate(self.user)
        config.set("enable_caching", True)
        uncached_response = self.client.get(reverse("categories-list"))
        cached_response = self.client.get(reverse("categories-list"))
        config.set("enable_caching", False)
        self.assertEqual(uncached_response.data, cached_response.data)

    def test_category_list_content_preevent_cached(self):
        self.client.force_authenticate(self.user)
        config.set("enable_preevent_cache", True)
        config.set("start_time", time.time() - 5)
        caches["default"].set("preevent_cache", {"key": "value"})
        cached_response = self.client.get(reverse("categories-list"))
        config.set("enable_preevent_cache", False)
        self.assertEqual(cached_response.data["d"], {"key": "value"})

    def test_category_list_content_preevent_cached_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        config.set("enable_preevent_cache", True)
        caches["default"].set("preevent_cache", {"key": "value"})
        cached_response = self.client.get(reverse("categories-list"))
        config.set("enable_preevent_cache", False)
        self.assertNotEqual(cached_response.data["d"], {"key": "value"})


class ChallengeViewsetTestCase(ChallengeSetupMixin, APITestCase):
    def test_challenge_list_unauthenticated_permission(self):
        response = self.client.get(reverse("challenges-list"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_challenge_list_authenticated_permission(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_challenge_list_unauthenticated_content(self):
        response = self.client.get(reverse("challenges-list"))
        self.assertFalse(response.data["s"])
        self.assertEqual(response.data["m"], "not_authenticated")
        self.assertEqual(response.data["d"], "")

    def test_challenge_list_authenticated_content(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertEqual(len(response.data), 3)

    def test_challenge_list_challenge_redacting(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertFalse("description" in self.find_challenge_entry(self.challenge3, data=response.data))

    def test_challenge_list_challenge_redacting_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        self.assertTrue("description" in response.data[0])

    def test_challenge_list_challenge_unlocked_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-list"))
        # TODO: Don't depend on order
        self.assertFalse(self.find_challenge_entry(self.challenge1, data=response.data)["unlocked"])

    def test_single_challenge_redacting(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertFalse("description" in response.data)

    def test_single_challenge_admin_redacting(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertTrue("description" in response.data)

    def test_admin_unlocking(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertFalse(response.data["unlocked"])

    def test_user_post_detail(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("challenges-detail", kwargs={"pk": self.challenge1.pk}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_user_post_list(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("challenges-list"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_challenge(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("challenges-list"),
            data={
                "name": "test4",
                "category": self.category.id,
                "description": "abc",
                "challenge_type": "test",
                "challenge_metadata": {},
                "flag_type": "plaintext",
                "author": "ractf",
                "score": 1000,
                "unlock_requirements": "",
                "flag_metadata": {},
                "tags": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_create_challenge_unauthorized(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("challenges-list"),
            data={
                "name": "test4",
                "category": self.category.id,
                "description": "abc",
                "challenge_type": "test",
                "challenge_metadata": {},
                "flag_type": "plaintext",
                "author": "ractf",
                "score": 1000,
                "unlock_requirements": "a",
                "flag_metadata": {},
            },
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_challenge_metadata_saves(self):
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
        self.assertEqual(response.data["challenge_metadata"], metadata)

    def test_create_challenge_with_tags(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        self.client.post(
            reverse("challenges-list"),
            data={
                "name": "test5",
                "category": self.category.id,
                "description": "abc",
                "challenge_type": "test",
                "challenge_metadata": {},
                "flag_type": "plaintext",
                "author": "ractf",
                "score": 1000,
                "unlock_requirements": "",
                "flag_metadata": {},
                "tags": [{"text": "abc", "type": "abc"}, {"text": "123", "type": "123"}],
            },
            format="json",
        )

        self.assertEqual(len(Tag.objects.filter(challenge__name="test5")), 2)

    def test_update_challenge_with_tags(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("challenges-list"),
            data={
                "name": "test5",
                "category": self.category.id,
                "description": "abc",
                "challenge_type": "test",
                "challenge_metadata": {},
                "flag_type": "plaintext",
                "author": "ractf",
                "score": 1000,
                "unlock_requirements": "",
                "flag_metadata": {},
                "tags": [],
            },
            format="json",
        )
        self.client.patch(
            reverse("challenges-detail", kwargs={"pk": response.json()["d"]["id"]}),
            data={
                "name": "test5",
                "category": self.category.id,
                "description": "abc",
                "challenge_type": "test",
                "challenge_metadata": {},
                "flag_type": "plaintext",
                "author": "ractf",
                "score": 1000,
                "unlock_requirements": "",
                "flag_metadata": {},
                "tags": [{"text": "abc", "type": "abc"}, {"text": "123", "type": "123"}],
            },
            format="json",
        )

        self.assertEqual(len(Tag.objects.filter(challenge__name="test5")), 2)


class FlagCheckViewTestCase(ChallengeSetupMixin, APITestCase):
    def test_disable_flag_submission(self):
        self.client.force_authenticate(self.user)
        config.set("enable_flag_submission", False)
        response = self.client.post(reverse("check-flag"))
        config.set("enable_flag_submission", True)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_bad_request(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("check-flag"))
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_havent_solved_challenge(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("check-flag"),
            data={
                "challenge": self.challenge1.id,
                "flag": "a",
            },
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_incorrect_flag(self):
        self.client.force_authenticate(self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        self.client.post(reverse("submit-flag"), data)
        response = self.client.post(
            reverse("check-flag"),
            data={
                "challenge": self.challenge2.id,
                "flag": "a",
            },
        )
        self.assertEqual(response.data["m"], "incorrect_flag")

    def test_correct_flag(self):
        self.client.force_authenticate(self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        self.client.post(reverse("submit-flag"), data)
        response = self.client.post(reverse("check-flag"), data)
        self.assertEqual(response.data["m"], "correct_flag")

    def test_post_score_explanation(self):
        self.client.force_authenticate(self.user)
        self.challenge2.post_score_explanation = "test"
        self.challenge2.save()
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        self.client.post(reverse("submit-flag"), data)
        response = self.client.post(reverse("check-flag"), data)
        self.assertTrue("explanation" in response.data["d"])


class RecalculateTestCase(ChallengeSetupMixin, APITestCase):
    def test_score_recalculate(self):
        self.client.force_authenticate(self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        self.client.post(reverse("submit-flag"), data)
        self.user.refresh_from_db()
        old_points = self.user.points
        self.challenge2.score = 69
        self.challenge2.save()
        self.user.refresh_from_db()
        self.user = Member.objects.get(id=self.user.id)
        self.assertNotEqual(old_points, self.user.points)


class FileTestCase(ChallengeSetupMixin, APITestCase):

    def setUp(self) -> None:
        super(FileTestCase, self).setUp()
        self.file = SimpleUploadedFile("flag.txt", b"ractf{flag}")

    def test_upload_file(self):
        body = {"upload": self.file, "challenge": self.challenge1.id}
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("files-list"), body)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_upload_file_ignores_name(self):
        body = {"upload": self.file, "challenge": self.challenge1.id, "name": "notflag.txt"}
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("files-list"), body)
        self.assertEqual(response.json()["d"]["name"], "flag.txt")

    def test_upload_file_ignores_size(self):
        body = {"upload": self.file, "challenge": self.challenge1.id, "size": 50}
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("files-list"), body)
        self.assertEqual(response.json()["d"]["size"], 11)

    def test_upload_file_max_size(self):
        body = {"upload": self.file, "challenge": self.challenge1.id}
        self.client.force_authenticate(self.admin_user)
        settings.MAX_UPLOAD_SIZE = 10
        response = self.client.post(reverse("files-list"), body)
        settings.MAX_UPLOAD_SIZE = 1_000_000_000
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_upload_url(self):
        body = {"challenge": self.challenge1.id, "url": "https://ractf.co.uk/index.html", "name": "index.html",
                "size": 50, "md5": "abc"}
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("files-list"), body)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_upload_none(self):
        body = {"challenge": self.challenge1.id, "name": "index.html", "size": 50, "md5": "abc"}
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("files-list"), body)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_upload_file_delete(self):
        body = {"upload": self.file, "challenge": self.challenge1.id}
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("files-list"), body)
        pk = response.json()["d"]["id"]
        response = self.client.delete(reverse("files-detail", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

    def test_url_file_delete(self):
        body = {"challenge": self.challenge1.id, "url": "https://ractf.co.uk/index.html", "name": "index.html",
                "size": 50, "md5": "abc"}
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("files-list"), body)
        pk = response.json()["d"]["id"]
        response = self.client.delete(reverse("files-detail", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)


class ChallengeVoteTestCase(ChallengeSetupMixin, APITestCase):

    def test_vote(self):
        self.solve_challenge()
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "positive": True}
        response = self.client.post(reverse("vote"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_vote_unsolved(self):
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "positive": True}
        response = self.client.post(reverse("vote"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_vote_again_updates(self):
        self.solve_challenge()
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "positive": True}
        self.client.post(reverse("vote"), data)
        data = {"challenge": self.challenge2.id, "positive": False}
        self.client.post(reverse("vote"), data)
        votes = ChallengeVote.objects.filter(user=self.user, challenge=self.challenge2)
        self.assertEqual(votes[0].positive, False)

    def test_vote_again_deletes(self):
        self.solve_challenge()
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "positive": True}
        self.client.post(reverse("vote"), data)
        data = {"challenge": self.challenge2.id, "positive": False}
        self.client.post(reverse("vote"), data)
        votes = ChallengeVote.objects.filter(user=self.user, challenge=self.challenge2)
        self.assertEqual(len(votes), 1)


class ChallengeFeedbackTestCase(ChallengeSetupMixin, APITestCase):

    def test_feedback(self):
        self.solve_challenge()
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "feedback": "abc"}
        response = self.client.post(reverse("submit-feedback"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_feedback_unsolved(self):
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "feedback": "abc"}
        response = self.client.post(reverse("submit-feedback"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_feedback_again_updates(self):
        self.solve_challenge()
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "feedback": "abc"}
        self.client.post(reverse("submit-feedback"), data)
        data = {"challenge": self.challenge2.id, "feedback": "123"}
        self.client.post(reverse("submit-feedback"), data)
        votes = ChallengeFeedback.objects.filter(user=self.user, challenge=self.challenge2)
        self.assertEqual(votes[0].feedback, "123")

    def test_feedback_again_deletes(self):
        self.solve_challenge()
        self.client.force_authenticate(self.user)
        data = {"challenge": self.challenge2.id, "feedback": "abc"}
        self.client.post(reverse("submit-feedback"), data)
        data = {"challenge": self.challenge2.id, "feedback": "123"}
        self.client.post(reverse("submit-feedback"), data)
        votes = ChallengeFeedback.objects.filter(user=self.user, challenge=self.challenge2)
        self.assertEqual(len(votes), 1)
