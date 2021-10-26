"""Unit tests for challenge utils."""

from unittest import TestCase

from rest_framework.test import APITestCase

from challenges.sql import get_negative_votes, get_positive_votes
from challenges.views import get_cache_key
from config import config
from teams.models import Member


class CacheKeyTestCase(TestCase):
    """Tests for cache key generation."""

    def test_get_cache_key_no_team(self):
        """Test the cache key generates correctly with no team."""
        user = Member(username="cachekeytest", email="cachekeytest@example.com")
        self.assertTrue(get_cache_key(user).endswith("no_team"))


class SqlTestCase(APITestCase):
    """Tests for the raw sql."""

    def test_get_positive_votes_cached(self):
        """Test the positive votes are correctly cached."""
        config.set("enable_caching", True)
        first = get_positive_votes()
        second = get_positive_votes()
        config.set("enable_caching", False)
        self.assertEqual(first, second)

    def test_get_negative_votes_cached(self):
        """Test the negative votes are correctly cached."""
        config.set("enable_caching", True)
        first = get_negative_votes()
        second = get_negative_votes()
        config.set("enable_caching", False)
        self.assertEqual(first, second)
