from rest_framework.test import APITestCase

from challenge.models import Challenge
from challenge.tests.mixins import ChallengeSetupMixin
from config import config
from member.models import Member


class ChallengeTestCase(ChallengeSetupMixin, APITestCase):

    def test_missing_flag_type(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="",
            flag_metadata={"flag": "ractf{a}", "exclude_passes": []},
            author="",
            score=1000,
        )
        challenge.save()
        check = challenge.self_check()
        self.assertEqual(check[0]["issue"], "missing_flag_type")

    def test_invalid_flag_data_type(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            score=1000,
        )
        challenge.save()
        check = challenge.self_check()
        self.assertEqual(check[0]["issue"], "invalid_flag_data_type")

    def test_is_unlocked_null_user(self):
        self.assertEqual(self.challenge2.is_unlocked(None), False)

    def test_is_unlocked_and_requirement(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="5 6 AND",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, [5, 6]), True)

    def test_is_not_unlocked_and_requirement(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="5 6 AND",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, [5]), False)

    def test_is_unlocked_or_requirement_both(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="5 6 OR",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, [5, 6]), True)

    def test_is_unlocked_or_requirement_one(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="5 6 OR",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, [5]), True)

    def test_is_unlocked_or_requirement_neither(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="5 6 OR",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, []), False)

    def test_is_unlocked_invalid_or(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="OR",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, []), False)

    def test_is_unlocked_invalid_and(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="AND",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, []), False)

    def test_is_unlocked_invalid_instruction(self):
        challenge = Challenge(
            name="test5",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata=[],
            author="",
            unlock_requirements="XOR",
            score=1000,
        )
        challenge.save()
        self.assertEqual(challenge.is_unlocked(self.user, []), False)

    def test_get_unlocked_annotated_queryset_hiding(self):
        user = Member.objects.create(username="challenge-test5", email="challenge-test5@example.org", is_staff=True)
        config.set("enable_force_admin_2fa", True)
        result = Challenge.get_unlocked_annotated_queryset(user)
        config.set("enable_force_admin_2fa", False)
        self.assertEqual(len(result), 0)
