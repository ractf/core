from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)
from rest_framework.test import APITestCase

from admin.models import AuditLogEntry
from config import config
from member.models import Member


class ConfigTestCase(APITestCase):
    def setUp(self):
        user = Member(username="config-test", email="config-test@example.org")
        user.is_staff = True
        user.save()
        self.staff_user = user
        user2 = Member(username="config-test2", email="config-test2@example.org")
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
        response = self.client.post(
            reverse("config-pk", kwargs={"name": "test"}), data={"key": "test", "value": "test"}, format="json"
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_create(self):
        self.client.force_authenticate(self.staff_user)
        response = self.client.post(
            reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json"
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_update_post(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        self.assertEqual(config.get("test"), "test2")

    def test_update_post_bad_request(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        response = self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={}, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_update_patch(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.patch(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        self.assertEqual(config.get("test"), "test2")

    def test_update_patch_bad_request(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        response = self.client.patch(reverse("config-pk", kwargs={"name": "test"}), data={}, format="json")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_update_patch_list(self):
        self.client.force_authenticate(self.staff_user)
        config.set("testlist", ["test"])
        self.client.patch(reverse("config-pk", kwargs={"name": "testlist"}), data={"value": "test"}, format="json")
        self.assertEqual(config.get("testlist"), ["test", "test"])

    def test_update_post_creates_audit_log(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        entry = AuditLogEntry.objects.latest("pk")
        self.assertEqual(entry.action, "set_config")

    def test_update_post_creates_audit_log_with_correct_extra(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        entry = AuditLogEntry.objects.latest("pk")
        self.assertEqual(entry.extra, {"old_value": "test", "new_value": "test2"})

    def test_update_patch_creates_audit_log(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.patch(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        entry = AuditLogEntry.objects.latest("pk")
        self.assertEqual(entry.action, "set_config")

    def test_update_patch_creates_audit_log_with_correct_extra(self):
        self.client.force_authenticate(self.staff_user)
        self.client.post(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test"}, format="json")
        self.client.patch(reverse("config-pk", kwargs={"name": "test"}), data={"value": "test2"}, format="json")
        entry = AuditLogEntry.objects.latest("pk")
        self.assertEqual(entry.extra, {"old_value": "test", "new_value": "test2"})
