from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_403_FORBIDDEN,
)
from rest_framework.test import APITestCase

from config import config


class ConfigTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="config-test", email="config-test@example.org")
        user.is_staff = True
        user.save()
        self.staff_user = user
        user2 = get_user_model()(username="config-test2", email="config-test2@example.org")
        user2.save()
        self.user = user2

    def test_auth_unauthed(self):
        response = self.client.get(reverse("config-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_auth_authed(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("config-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_auth_authed_staff(self):
        self.client.force_authenticate(self.staff_user)
        response = self.client.get(reverse("config-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_get_sensitive_not_staff(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("config-pk", kwargs={"name": "enable_force_admin_2fa"}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_get_sensitive_staff(self):
        self.client.force_authenticate(self.staff_user)
        response = self.client.get(reverse("config-pk", kwargs={"name": "enable_force_admin_2fa"}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_post_authed(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"key": "test", "value": "test"}, format="json")
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create(self):
        self.client.force_authenticate(self.staff_user)
        response = self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_update(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        response = self.client.patch(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(config.get("test"), "test2")
