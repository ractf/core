from unittest import TestCase

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from challenge.models import Challenge, File, get_file_name
from challenge.sql import get_negative_votes, get_positive_votes
from challenge.tests.mixins import ChallengeSetupMixin
from challenge.views import get_cache_key
from config import config


class CacheKeyTestCase(TestCase):
    def test_get_cache_key_no_team(self):
        user = get_user_model()(username="cachekeytest", email="cachekeytest@example.com")
        self.assertTrue(get_cache_key(user).endswith("no_team"))


class SqlTestCase(APITestCase):
    def test_get_positive_votes_cached(self):
        config.set("enable_caching", True)
        first = get_positive_votes()
        second = get_positive_votes()
        config.set("enable_caching", False)
        self.assertEqual(first, second)

    def test_get_negative_votes_cached(self):
        config.set("enable_caching", True)
        first = get_negative_votes()
        second = get_negative_votes()
        config.set("enable_caching", False)
        self.assertEqual(first, second)


class FileTestCase(ChallengeSetupMixin, APITestCase):

    def test_get_filename(self):
        md5 = "12345678901234567890123456789012"
        file = File(challenge=self.challenge1, md5=md5)
        self.assertEqual(get_file_name(file, "filename"), f"{self.challenge1.id}/{md5}/filename")

