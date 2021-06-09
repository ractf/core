from unittest import TestCase

from django.contrib.auth import get_user_model

from challenge.views import get_cache_key


class CacheKeyTestCase(TestCase):
    def test_get_cache_key_no_team(self):
        user = get_user_model()(username="cachekeytest", email="cachekeytest@example.com")
        self.assertTrue(get_cache_key(user).endswith("no_team"))
