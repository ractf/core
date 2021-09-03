"""Tests related to login functionality."""

from unittest import mock

import pyotp
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication import views
from authentication.models import BackupCode, Token, TOTPDevice
from authentication.tests import utils
from config import config
from teams.models import Member


class LogoutTestCase(APITestCase):
    """Tests related to the logout endpoint."""

    def setUp(self):
        """Create a user for testing."""
        user = Member(username="logout-test", email="logout-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user

    def test_logout(self):
        """An authenticated user logging out should return 200."""
        self.client.post(reverse("login"), data={"username": self.user.username, "password": "password", "otp": ""})
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_not_logged_in(self):
        """An unauthenticated user logging out should return 401."""
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LoginTestCase(APITestCase):
    """Tests related to the login endpoint."""

    def setUp(self):
        """Create a user for testing."""
        user = Member(username="login-test", email="login-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user
        views.LoginView.throttle_scope = ""

    def test_login(self):
        """Logging in with valid credentials should return 200."""
        self.user.set_password("password")
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_invalid(self):
        """Logging in with invalid credentials should return 401."""
        data = {
            "username": "login-test",
            "password": "a",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_data(self):
        """Logging in with a malfored request should return 400."""
        data = {
            "username": "login-test",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_email_not_verified(self):
        """Logging in without a verified email should return 401."""
        self.user.email_verified = False
        self.user.save()
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch("time.time", side_effect=utils.get_fake_time)
    def test_login_login_closed(self, mock_obj):
        """Logging in when login is closed should return 401."""
        data = {
            "username": "login-test",
            "password": "password",
        }
        config.set("enable_prelogin", False)
        response = self.client.post(reverse("login"), data)
        config.set("enable_prelogin", True)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive(self):
        """Logging in with an inactive account should return 401."""
        self.user.is_active = False
        self.user.save()
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.user.is_active = True
        self.user.save()

    def test_login_with_email(self):
        """Logging in with valid credentials, but using email, should return 200."""
        self.user.set_password("password")
        data = {
            "username": "login-test@example.org",
            "password": "password",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_wrong_user(self):
        """Logging in with an incorrect username should return 401."""
        data = {
            "username": "login-",
            "password": "password",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_wrong_password(self):
        """Logging in with an incorrect password should return 401."""
        data = {
            "username": "login-test",
            "password": "passw",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_malformed(self):
        """Logging in with a malformed request should return 400."""
        data = {
            "username": "login-test",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_2fa_required(self):
        """Test logging in with no 2fa code when 2fa is active returns 401."""
        TOTPDevice(user=self.user, verified=True).save()
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class Login2FATestCase(APITestCase):
    """Tests for the login 2fa view."""

    def setUp(self):
        """Create a user with 2fa enabled for testing."""
        user = Member(username="login-test", email="login-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        TOTPDevice(user=user, verified=True).save()
        self.user = user
        views.LoginTwoFactorView.throttle_scope = ""

    def test_login_2fa(self):
        """Logging in with correct credentials and 2fa should return 200."""
        secret = TOTPDevice.objects.get(user=self.user).totp_secret
        totp = pyotp.TOTP(secret)
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": totp.now(),
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_2fa_invalid(self):
        """
        Logging in with correct credentials and incorrect 2fa should return 200.

        Regression test for CVE-2021-21329.
        """
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "123456",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_2fa_without_2fa(self):
        """Logging in using the 2fa view when 2fa is not enabled should return 401."""
        user = Member(username="login-test-no-2fa", email="login-test-no-2fa@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        data = {"username": "login-test-no-2fa", "password": "password", "tfa": "123456"}
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_2fa_missing(self):
        """Logging in without a 2fa code should return 400."""
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_2fa_backup_code(self):
        """Logging in with correct credentials and a backup code should return 200."""
        BackupCode(user=self.user, code="12345678").save()
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "12345678",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_2fa_backup_code_invalid(self):
        """Logging in with correct credentials and an invalid backup code should return 401."""
        BackupCode(user=self.user, code="12345678").save()
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "87654321",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_2fa_invalid_code(self):
        """
        Logging in with correct credentials but a 2fa code that isnt possibly valid should return 401.

        Regression test for CVE-2021-21329.
        """
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "123456789",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenTestCase(APITestCase):
    """Tests for the Token database model."""

    def test_token_str(self):
        """The string representation should be equal to the token value."""
        user = Member(username="token-test", email="token-test@example.org")
        user.save()
        tok = Token(key="a" * 40, user=user)
        self.assertEqual(str(tok), "a" * 40)

    def test_token_preserves_key(self):
        """Saving a token should not change its value."""
        user = Member(username="token-test-2", email="token-test-2@example.org")
        user.save()
        token = Token(key="a" * 40, user=user)
        token.save()
        self.assertEqual(token.key, "a" * 40)


class TFATestCase(APITestCase):
    """Tests for api endpoints that manage 2fa."""

    def setUp(self):
        """Create a user for testing and remove ratelimits."""
        user = Member(username="2fa-test", email="2fa-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user
        views.AddTwoFactorView.throttle_scope = ""
        views.VerifyTwoFactorView.throttle_scope = ""

    def test_add_2fa_unauthenticated(self):
        """Adding 2fa when not logged in should return 401."""
        response = self.client.post(reverse("add-2fa"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_2fa(self):
        """Adding 2fa when authenticated should add a totp device, but not active 2fa."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        self.assertFalse(self.user.has_2fa())
        self.assertNotEqual(self.user.totp_device, None)

    def test_add_2fa_twice(self):
        """Adding 2fa twice should overwrite the original totp device."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        response = self.client.post(reverse("add-2fa"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_2fa(self):
        """Verifying a totp device should activate totp on that user."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        secret = self.user.totp_device.totp_secret
        totp = pyotp.TOTP(secret)
        self.client.post(reverse("verify-2fa"), data={"otp": totp.now()})
        self.assertTrue(self.user.has_2fa())

    def test_verify_2fa_invalid(self):
        """Verifying 2fa with an invalid code should be rejected."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        self.client.post(reverse("verify-2fa"), data={"otp": "123456"})
        self.assertFalse(self.user.totp_device.verified)

    def test_add_2fa_with_2fa(self):
        """Adding 2fa when 2fa is already verified should return 403."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        secret = self.user.totp_device.totp_secret
        totp = pyotp.TOTP(secret)
        self.client.post(reverse("verify-2fa"), data={"otp": totp.now()})
        response = self.client.post(reverse("add-2fa"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_2fa(self):
        """Removing 2fa with a valid 2fa code should return 200."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = Member.objects.get(id=self.user.pk).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        response = self.client.post(reverse("remove-2fa"), data={"otp": pyotp.TOTP(totp_device.totp_secret).now()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_remove_2fa_fail(self):
        """Removing 2fa with an invalid 2fa code should return 401."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = Member.objects.get(id=self.user.pk).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        response = self.client.post(reverse("remove-2fa"), data={"otp": "invalid_otp"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_2fa_removes_2fa(self):
        """Removing 2fa with a valid 2fa code should disable 2fa on the user."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = Member.objects.get(id=self.user.pk).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        self.client.post(reverse("remove-2fa"), data={"otp": pyotp.TOTP(totp_device.totp_secret).now()})
        self.assertFalse(Member.objects.get(id=self.user.pk).has_2fa())

    def test_remove_2fa_no_2fa(self):
        """Removing 2fa without active 2fa should return 403."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        user = Member.objects.get(id=self.user.pk)
        user.totp_device = None
        user.save()
        response = self.client.post(reverse("remove-2fa"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
