from django.urls import reverse
from rest_framework.test import APITestCase
from config import config

from team.tests import TeamSetupMixin
from requests.exceptions import ConnectionError


class AndromedaTestCase(TeamSetupMixin, APITestCase):
    def test_get_instance_disabled_challenge_server(self):
        with self.settings(
            CHALLENGE_SERVER_ENABLED=False,
        ):
            self.client.force_authenticate(user=self.user)
            response = self.client.get(reverse("get-instance", args=["1"]))
            self.assertContains(response, "challenge_server_disabled", status_code=403)

    def test_request_new_instance_disabled_challenge_server(self):
        with self.settings(
            CHALLENGE_SERVER_ENABLED=False,
        ):
            self.client.force_authenticate(user=self.user)
            response = self.client.get(reverse("request-new-instance", args=["1"]))
            self.assertContains(response, "challenge_server_disabled", status_code=403)

    def test_get_instance_no_team(self):
        with self.settings(
            CHALLENGE_SERVER_ENABLED=True,
        ):
            self.client.force_authenticate(user=self.user)
            config.set("enable_team_leave", True)
            self.client.post(reverse("team-leave"))
            response = self.client.get(reverse("get-instance", args=["1"]))
            self.assertContains(response, "challenge_server_team_required", status_code=403)

    def test_get_instance(self):
        # This is a bad test but we need a stub service
        with self.settings(
            CHALLENGE_SERVER_ENABLED=True,
            ANDROMEDA_URL="http://andromeda",
            ANDROMEDA_API_KEY="andromeda",
            ANDROMEDA_TIMEOUT=0.1,
        ):
            with self.assertRaises(ConnectionError):
                self.client.force_authenticate(user=self.user)
                self.client.get(reverse("get-instance", args=["1"]))
