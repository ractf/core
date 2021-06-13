"""Test any password or password-reset related logic in authentication."""

from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication import views
from authentication.models import PasswordResetToken
from config import config
from member.models import Member


class RequestPasswordResetTestCase(APITestCase):
    def setUp(self):
        views.RequestPasswordResetView.throttle_scope = ""

    def test_password_reset_request_invalid(self):
        response = self.client.post(reverse("request-password-reset"), data={"email": "user10@example.org"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_request_valid(self):
        with self.settings(
            MAIL={"SEND_ADDRESS": "no-reply@ractf.co.uk", "SEND_NAME": "RACTF", "SEND": True, "SEND_MODE": "SES"}
        ):
            Member(username="test-password-rest", email="user10@example.org", email_verified=True).save()
            response = self.client.post(reverse("request-password-reset"), data={"email": "user10@example.org"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class DoPasswordResetTestCase(APITestCase):
    def setUp(self):
        user = Member(username="pr-test", email="pr-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        PasswordResetToken(user=user, token="testtoken").save()
        self.user = user
        views.DoPasswordResetView.throttle_scope = ""

    def test_password_reset(self):
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_issues_token(self):
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        print(response.data)
        self.assertTrue("token" in response.data["d"])

    def test_password_reset_bad_token(self):
        data = {
            "uid": self.user.pk,
            "token": "abc",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_password_reset_weak_password(self):
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "password",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_login_disabled(self):
        config.set("enable_login", False)
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        config.set("enable_login", True)
        self.assertFalse("token" in response.data["d"])

    @mock.patch("time.time", side_effect=utils.get_fake_time)
    def test_password_reset_cant_login_yet(self, obj):
        config.set("enable_prelogin", False)
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        config.set("enable_prelogin", True)
        self.assertFalse("token" in response.data["d"])


class ChangePasswordTestCase(APITestCase):
    def setUp(self):
        user = Member(username="cp-test", email="cp-test@example.org")
        user.set_password("password")
        user.save()
        self.user = user
        views.ChangePasswordView.throttle_scope = ""

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "password",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("change-password"), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_weak(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "password",
            "password": "password",
        }
        response = self.client.post(reverse("change-password"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_invalid_old(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "passwordddddddd",
            "password": "password",
        }
        response = self.client.post(reverse("change-password"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
