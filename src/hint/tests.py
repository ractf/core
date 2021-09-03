"""Tests for the hint app."""

from challenges.tests.mixins import ChallengeSetupMixin
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from hint.views import HintViewSet, UseHintView


class HintTestCase(ChallengeSetupMixin, APITestCase):
    """Tests for the hints."""

    def setUp(self):
        """Remove ratelimits from endpoints."""
        super().setUp()
        HintViewSet.throttle_scope = ""
        UseHintView.throttle_scope = ""

    def test_hint_view(self):
        """Test a user cannot access a hint they haven't unlocked."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-detail", kwargs={"pk": self.hint1.pk}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_view_admin(self):
        """Test an admin can access a hint they haven't unlocked."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-detail", kwargs={"pk": self.hint1.pk}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_list(self):
        """Test a user can view the hint list."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_list_redaction(self):
        """Test a user cannot view the details of a hint they haven't unlocked."""
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertEqual(response.data[0]["text"], "")

    def test_hint_list_admin(self):
        """Test an admin can access the list of hints."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_list_redaction_admin(self):
        """Test an admin can view details of hints they haven't unlocked."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertTrue("text" in response.data[0])

    def test_hint_post(self):
        """Test a non-admin user cannot create a hint."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("hint-list"),
            data={"name": "test-hint", "penalty": 100, "challenge": self.challenge2.pk},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_detail_put(self):
        """Test a non-admin user cannot modify a hint."""
        self.client.force_authenticate(self.user)
        response = self.client.put(
            reverse("hint-detail", kwargs={"pk": self.hint1.pk}),
            data={"name": "test-hint"},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_post_admin(self):
        """Test an admin user can create a hint."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("hint-list"),
            data={
                "name": "test-hint",
                "penalty": 100,
                "challenge": self.challenge2.pk,
                "text": "abc",
            },
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_hint_detail_patch_admin(self):
        """Test an admin user can modify a hint."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("hint-detail", kwargs={"pk": self.hint3.pk}),
            data={"name": "test-hint"},
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_detail_patch(self):
        """Test a normal user cannot patch a hint."""
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("hint-detail", kwargs={"pk": self.hint3.pk}),
            data={"name": "test-hint"},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_use(self):
        """Test a user can use a hint."""
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("hint-use"), data={"id": self.hint3.pk})
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_use_read(self):
        """Test a user can read a hint once they've used it."""
        self.client.force_authenticate(self.user)
        self.client.post(reverse("hint-use"), data={"id": self.hint3.pk})
        response = self.client.get(reverse("hint-detail", kwargs={"pk": self.hint3.pk}))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertNotEqual(response.data["text"], "")

    def test_hint_use_duplicate(self):
        """Test a user cannot redeem a hint twice."""
        self.client.force_authenticate(self.user)
        self.client.post(reverse("hint-use"), data={"id": self.hint3.pk})
        response = self.client.post(reverse("hint-use"), data={"id": self.hint3.pk})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_use_locked(self):
        """Test a user cannot use a hint that is on a locked challenge."""
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("hint-use"), data={"id": self.hint1.pk})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
