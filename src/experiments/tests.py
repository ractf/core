from django.urls import reverse
from rest_framework.test import APITestCase


class ExperimentsTestCase(APITestCase):
    def test_experiments(self):
        with self.settings(EXPERIMENT_OVERRIDES={"test": True}):
            response = self.client.get(reverse("experiments"))
            self.assertEqual(response.data["d"]["test"], True)
