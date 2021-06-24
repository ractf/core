"""Test any password or password-reset related logic in authentication."""
import time
from unittest import mock

from django.urls import reverse
from member.models import Member
from rest_framework import status
from rest_framework.test import APITestCase

from authentication import views
from authentication.models import PasswordResetToken
from authentication.tests import utils
from config import config


class RequestPasswordResetTestCase(APITestCase):
    """Tests related to requesting a password reset."""

    def setUp(self):
        """Remove the ratelimit."""
        views.RequestPasswordResetView.throttle_scope = ""

    def test_password_reset_request_invalid(self):
        """Requesting a password reset on an invalid email should return 200."""
        response = self.client.post(reverse("request-password-reset"), data={"email": "user10@example.org"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_request_valid(self):
        """Requesting a password reset on a valid email should return 200."""
        with self.settings(
            MAIL={"SEND_ADDRESS": "no-reply@ractf.co.uk", "SEND_NAME": "RACTF", "SEND": True, "SEND_MODE": "SES"}
        ):
            Member(username="test-password-rest", email="user10@example.org", email_verified=True).save()
            response = self.client.post(reverse("request-password-reset"), data={"email": "user10@example.org"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class DoPasswordResetTestCase(APITestCase):
    """Tests related to completing a password reset."""

    def setUp(self):
        """Remove the ratelimit and create a test user."""
        user = Member(username="pr-test", email="pr-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        PasswordResetToken(user=user, token="testtoken").save()
        self.user = user
        views.DoPasswordResetView.throttle_scope = ""

    def test_password_reset(self):
        """Completing a password reset should return 200."""
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_issues_token(self):
        """Completing a password reset should issue a token."""
        config.set("start_time", time.time() - 50000)
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        print(response.data)
        self.assertTrue("token" in response.data["d"])

    def test_password_reset_bad_token(self):
        """Attempting a password reset with an invalid token should 404."""
        data = {
            "uid": self.user.pk,
            "token": "abc",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_password_reset_weak_password(self):
        """Weak passwords should be rejected."""
        data = {
            "uid": self.user.pk,
            "token": "testtoken",
            "password": "password",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_login_disabled(self):
        """Tokens should not be issued when login is disabled."""
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
        """Tokens should not be issued before login is enabled."""
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
    """Tests related to changing passwords."""

    def setUp(self):
        """Create a user for testing."""
        user = Member(username="cp-test", email="cp-test@example.org")
        user.set_password("password")
        user.save()
        self.user = user
        views.ChangePasswordView.throttle_scope = ""

    def test_change_password(self):
        """Changing the password should return 200."""
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "password",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("change-password"), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_weak(self):
        """Setting a weak password should be denied."""
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "password",
            "password": "password",
        }
        response = self.client.post(reverse("change-password"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_invalid_old(self):
        """Changing a password with an incorrect old password should be denied."""
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "passwordddddddd",
            "password": "password",
        }
        response = self.client.post(reverse("change-password"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
