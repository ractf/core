from rest_framework.reverse import reverse
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_200_OK, HTTP_201_CREATED
from rest_framework.test import APITestCase

from challenge.tests import ChallengeSetupMixin
from hint.views import HintViewSet, UseHintView


class HintTestCase(ChallengeSetupMixin, APITestCase):

    def setUp(self):
        super().setUp()
        HintViewSet.throttle_scope = ''
        UseHintView.throttle_scope = ''

    def test_hint_view(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-detail", kwargs={"pk": self.hint1.id}))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_view_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-detail", kwargs={"pk": self.hint1.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_list(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_list_redaction(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertEqual(response.data[0]["text"], "")

    def test_hint_list_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_list_redaction_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("hint-list"))
        self.assertTrue("text" in response.data[0])

    def test_hint_post(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("hint-list"),
            data={"name": "test-hint", "penalty": 100, "challenge": self.challenge2.id},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_detail_put(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(
            reverse("hint-detail", kwargs={"pk": self.hint1.id}),
            data={"name": "test-hint"},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_post_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("hint-list"),
            data={
                "name": "test-hint",
                "penalty": 100,
                "challenge": self.challenge2.id,
                "text": "abc",
            },
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_hint_detail_patch_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("hint-detail", kwargs={"pk": self.hint3.id}),
            data={"name": "test-hint"},
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_detail_patch(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("hint-detail", kwargs={"pk": self.hint3.id}),
            data={"name": "test-hint"},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_use(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("hint-use"), data={"id": self.hint3.id})
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_hint_use_read(self):
        self.client.force_authenticate(self.user)
        self.client.post(reverse("hint-use"), data={"id": self.hint3.id})
        response = self.client.get(reverse("hint-detail", kwargs={"pk": self.hint3.id}))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertNotEquals(response.data["text"], "")

    def test_hint_use_duplicate(self):
        self.client.force_authenticate(self.user)
        self.client.post(reverse("hint-use"), data={"id": self.hint3.id})
        response = self.client.post(reverse("hint-use"), data={"id": self.hint3.id})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_hint_use_locked(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("hint-use"), data={"id": self.hint1.id})
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
