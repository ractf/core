"""Tests for the config app."""

from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)
from rest_framework.test import APITestCase

from config import config


class ConfigTestCase(APITestCase):
    """Tests for the config api routes."""

    def setUp(self):
        """Set up some users for use in tests."""
        user = get_user_model()(username="config-test", email="config-test@example.org")
        user.is_staff = True
        user.save()
        self.staff_user = user
        user2 = get_user_model()(username="config-test2", email="config-test2@example.org")
        user2.save()
        self.user = user2

    def test_auth_unauthed(self):
        """Check unauthenticated users can access the full config."""
        response = self.client.get(reverse("config-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_auth_authed(self):
        """Check authenticated users can access the full config."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("config-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_auth_authed_staff(self):
        """Check authenticated admin users can access the full config."""
        self.client.force_authenticate(self.staff_user)
        response = self.client.get(reverse("config-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_get_sensitive_not_staff(self):
        """Check authenticated non-admin users cannot access sensitive config keys."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("config-pk", kwargs={"name": "enable_force_admin_2fa"}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_get_sensitive_staff(self):
        """Check authenticated admin users can access sensitive config keys."""
        self.client.force_authenticate(self.staff_user)
        response = self.client.get(reverse("config-pk", kwargs={"name": "enable_force_admin_2fa"}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_post_authed(self):
        """Test a non-admin user cannot create config keys."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("config-pk", kwargs={"name": "test"}), data={"key": "test", "value": "test"}, format="json"
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create(self):
        """Test a admin user can create config keys."""
        self.client.force_authenticate(self.staff_user)
        response = self.client.post(
            reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json"
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_update_post(self):
        """Test an admin user can update config keys."""
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        self.assertEqual(config.get("test"), "test2")

    def test_update_post_bad_request(self):
        """Test a malformed config update is rejected."""
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        response = self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={}, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_update_patch(self):
        """Test a config key can be modified with a patch request."""
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.patch(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        self.assertEqual(config.get("test"), "test2")

    def test_update_patch_bad_request(self):
        """Test a malformed patch request is rejected."""
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        response = self.client.patch(reverse("config-pk", kwargs={"name": "test"}), data={}, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_update_patch_list(self):
        """Test a patch request correctly appends to a list."""
        self.client.force_authenticate(self.staff_user)
        config.set("testlist", ["test"])
        self.client.patch(reverse("config-pk", kwargs={"name": "testlist"}), data={"value": "test"}, format="json")
        self.assertEqual(config.get("testlist"), ["test", "test"])
