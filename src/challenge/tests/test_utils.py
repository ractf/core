from unittest import TestCase

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from challenge.sql import get_negative_votes, get_positive_votes
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
