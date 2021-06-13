from unittest import mock

import pyotp
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication import utils, views
from authentication.models import BackupCode, Token, TOTPDevice
from config import config
from member.models import Member


class LogoutTestCase(APITestCase):
    def setUp(self):
        user = Member(username="logout-test", email="logout-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user

    def test_logout(self):
        self.client.post(reverse("login"), data={"username": self.user.username, "password": "password", "otp": ""})
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_not_logged_in(self):
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LoginTestCase(APITestCase):
    def setUp(self):
        user = Member(username="login-test", email="login-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user
        views.LoginView.throttle_scope = ""

    def test_login(self):
        self.user.set_password("password")
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_invalid(self):
        data = {
            "username": "login-test",
            "password": "a",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_data(self):
        data = {
            "username": "login-test",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_email_not_verified(self):
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
        data = {
            "username": "login-test",
            "password": "password",
        }
        config.set("enable_prelogin", False)
        response = self.client.post(reverse("login"), data)
        config.set("enable_prelogin", True)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive(self):
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
        self.user.set_password("password")
        data = {
            "username": "login-test@example.org",
            "password": "password",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_wrong_user(self):
        data = {
            "username": "login-",
            "password": "password",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_wrong_password(self):
        data = {
            "username": "login-test",
            "password": "passw",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_malformed(self):
        data = {
            "username": "login-test",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_2fa_required(self):
        TOTPDevice(user=self.user, verified=True).save()
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class Login2FATestCase(APITestCase):
    def setUp(self):
        user = Member(username="login-test", email="login-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        TOTPDevice(user=user, verified=True).save()
        self.user = user
        views.LoginTwoFactorView.throttle_scope = ""

    def test_login_2fa(self):
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
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "123456",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_2fa_without_2fa(self):
        user = Member(username="login-test-no-2fa", email="login-test-no-2fa@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        data = {"username": "login-test-no-2fa", "password": "password", "tfa": "123456"}
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_2fa_missing(self):
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_2fa_backup_code(self):
        BackupCode(user=self.user, code="12345678").save()
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "12345678",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_2fa_backup_code_invalid(self):
        BackupCode(user=self.user, code="12345678").save()
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "87654321",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_2fa_invalid_code(self):
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "123456789",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenTestCase(APITestCase):
    def test_token_str(self):
        user = Member(username="token-test", email="token-test@example.org")
        user.save()
        tok = Token(key="a" * 40, user=user)
        self.assertEqual(str(tok), "a" * 40)

    def test_token_preserves_key(self):
        user = Member(username="token-test-2", email="token-test-2@example.org")
        user.save()
        token = Token(key="a" * 40, user=user)
        token.save()
        self.assertEqual(token.key, "a" * 40)


class TFATestCase(APITestCase):
    def setUp(self):
        user = Member(username="2fa-test", email="2fa-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user
        views.AddTwoFactorView.throttle_scope = ""
        views.VerifyTwoFactorView.throttle_scope = ""

    def test_add_2fa_unauthenticated(self):
        response = self.client.post(reverse("add-2fa"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(self.user.has_2fa())

    def test_add_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        self.assertFalse(self.user.has_2fa())
        self.assertNotEqual(self.user.totp_device, None)

    def test_add_2fa_twice(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        response = self.client.post(reverse("add-2fa"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        secret = self.user.totp_device.totp_secret
        totp = pyotp.TOTP(secret)
        self.client.post(reverse("verify-2fa"), data={"otp": totp.now()})
        self.assertTrue(self.user.has_2fa())

    def test_verify_2fa_invalid(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        self.client.post(reverse("verify-2fa"), data={"otp": "123456"})
        self.assertFalse(self.user.totp_device.verified)

    def test_add_2fa_with_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        secret = self.user.totp_device.totp_secret
        totp = pyotp.TOTP(secret)
        self.client.post(reverse("verify-2fa"), data={"otp": totp.now()})
        response = self.client.post(reverse("add-2fa"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = Member.objects.get(id=self.user.pk).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        response = self.client.post(reverse("remove-2fa"), data={"otp": pyotp.TOTP(totp_device.totp_secret).now()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_remove_2fa_fail(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = Member.objects.get(id=self.user.pk).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        response = self.client.post(reverse("remove-2fa"), data={"otp": "invalid_otp"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_2fa_removes_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = Member.objects.get(id=self.user.pk).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        self.client.post(reverse("remove-2fa"), data={"otp": pyotp.TOTP(totp_device.totp_secret).now()})
        self.assertFalse(Member.objects.get(id=self.user.pk).has_2fa())

    def test_remove_2fa_no_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        user = Member.objects.get(id=self.user.pk)
        user.totp_device = None
        user.save()
        response = self.client.post(reverse("remove-2fa"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
