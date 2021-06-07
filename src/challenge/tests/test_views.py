from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from challenge.models import Solve
from challenge.tests.mixins import ChallengeSetupMixin
from config import config
from hint.models import HintUse


class ChallengeTestCase(ChallengeSetupMixin, APITestCase):
    def solve_challenge(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        return self.client.post(reverse("submit-flag"), data)

    def test_challenge_solve(self):
        response = self.solve_challenge()
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["d"]["correct"], True)

    def test_challenge_solve_incorrect_flag(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "flag": "ractf{b}",
            "challenge": self.challenge2.id,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["d"]["correct"], False)

    def test_challenge_double_solve(self):
        self.solve_challenge()
        self.client.force_authenticate(user=self.user2)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_challenge_unlocks(self):
        self.solve_challenge()
        self.challenge1.unlock_requirements = str(self.challenge2.id)
        self.assertTrue(self.challenge1.is_unlocked(get_user_model().objects.get(id=self.user.id)))

    def test_challenge_unlocks_no_team(self):
        user4 = get_user_model()(username="challenge-test-4", email="challenge-test-4@example.org")
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
            "challenge": self.challenge2.id,
        }
        self.client.post(reverse("submit-flag"), data)
        self.client.force_authenticate(user=self.user2)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_challenge_score_not_first_blood(self):
        self.solve_challenge()
        self.client.force_authenticate(user=self.user3)
        data = {
            "flag": "ractf{a}",
            "challenge": self.challenge2.id,
        }
        response = self.client.post(reverse("submit-flag"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(Solve.objects.get(team=self.team2, challenge=self.challenge2).first_blood)

    def test_challenge_solved_unauthed(self):
        self.assertFalse(self.challenge2.is_solved(AnonymousUser()))

    def test_challenge_unlocked_unauthed(self):
        self.assertFalse(self.challenge2.is_unlocked(AnonymousUser()))

    def test_challenge_solved_no_team(self):
        user4 = get_user_model()(username="challenge-test-4", email="challenge-test-4@example.org")
        user4.save()
        self.assertFalse(self.challenge2.is_solved(user4))


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
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertFalse("description" in self.get_json_for(self.challenge1, data=response.data))

    def test_category_list_challenge_redacting_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertFalse("description" in self.get_json_for(self.challenge3, data=response.data))

    def test_category_list_challenge_unlocked_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("categories-list"))
        self.assertFalse(self.get_json_for(self.challenge1, data=response.data))

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
        self.assertFalse("description" in response.data[-1])

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
        self.assertFalse(response.data[-1]["unlocked"])

    def test_single_challenge_redacting(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.id}))
        self.assertFalse("description" in response.data)

    def test_single_challenge_admin_redacting(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.id}))
        self.assertTrue("description" in response.data)

    def test_admin_unlocking(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("challenges-detail", kwargs={"pk": self.challenge1.id}))
        self.assertFalse(response.data["unlocked"])

    def test_user_post_detail(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("challenges-detail", kwargs={"pk": self.challenge1.id}))
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
                "author": "dave",
                "score": 1000,
                "unlock_requirements": "a",
                "flag_metadata": {},
            },
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
