from unittest import mock

import pyotp
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.test import APITestCase

from authentication.models import (
    BackupCode,
    InviteCode,
    PasswordResetToken,
    Token,
    TOTPDevice,
)
from authentication.views import (
    AddTwoFactorView,
    ChangePasswordView,
    CreateBotView,
    DoPasswordResetView,
    LoginTwoFactorView,
    LoginView,
    RegenerateBackupCodesView,
    RegistrationView,
    RequestPasswordResetView,
    VerifyEmailView,
    VerifyTwoFactorView,
)
from config import config
from team.models import Team


def get_fake_time():
    return 0


class RegisterTestCase(APITestCase):
    def setUp(self):
        RegistrationView.throttle_scope = ""

    def test_register(self):
        data = {
            "username": "user1",
            "password": "uO7*$E@0ngqL",
            "email": "user@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_register_with_mail(self):
        with self.settings(MAIL={"SEND_ADDRESS": "no-reply@ractf.co.uk", "SEND_NAME": "RACTF", "SEND": True, "SEND_MODE": "SES"}):
            data = {
                "username": "user1",
                "password": "uO7*$E@0ngqL",
                "email": "user@example.org",
            }
            response = self.client.post(reverse("register"), data)
            self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_register_weak_password(self):
        data = {
            "username": "user2",
            "password": "password",
            "email": "user2@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        data = {
            "username": "user3",
            "password": "uO7*$E@0ngqL",
            "email": "user3@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        data = {
            "username": "user3",
            "password": "uO7*$E@0ngqL",
            "email": "user4@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        data = {
            "username": "user4",
            "password": "uO7*$E@0ngqL",
            "email": "user4@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        data = {
            "username": "user5",
            "password": "uO7*$E@0ngqL",
            "email": "user4@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @mock.patch("time.time", side_effect=get_fake_time)
    def test_register_closed(self, mock_obj):
        config.set("enable_prelogin", False)
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        config.set("enable_prelogin", True)

    def test_register_admin(self):
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6@example.org",
        }
        self.client.post(reverse("register"), data)
        self.assertTrue(get_user_model().objects.filter(username=data["username"]).first().is_staff)

    def test_register_second(self):
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6@example.org",
        }
        self.client.post(reverse("register"), data)
        data = {
            "username": "user7",
            "password": "uO7*$E@0ngqL",
            "email": "user7@example.org",
        }
        self.client.post(reverse("register"), data)
        self.assertFalse(get_user_model().objects.filter(username=data["username"]).first().is_staff)

    def test_register_malformed(self):
        data = {
            "username": "user6",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_invalid_email(self):
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_teams_disabled(self):
        config.set("enable_teams", False)
        data = {
            "username": "user10",
            "password": "uO7*$E@0ngqL",
            "email": "user10@example.com",
        }
        response = self.client.post(reverse("register"), data)
        config.set("enable_teams", True)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.get(username="user10").team.name, "user10")


class EmailResendTestCase(APITestCase):
    def test_email_resend(self):
        with self.settings(RATELIMIT_ENABLE=False):
            user = get_user_model()(username="test_verify_user", email_verified=False, email="tvu@example.com")
            user.save()
            response = self.client.post(reverse("resend-email"), {"email": "tvu@example.com"})
            self.assertEqual(response.status_code, HTTP_200_OK)

    def test_already_verified_email_resend(self):
        with self.settings(RATELIMIT_ENABLE=False):
            user = get_user_model()(username="resend-email", email_verified=True, email="tvu@example.com")
            user.save()
            response = self.client.post(reverse("resend-email"), {"email": "tvu@example.com"})
            self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_non_existing_email_resend(self):
        with self.settings(RATELIMIT_ENABLE=False):
            response = self.client.post(reverse("resend-email"), {"email": "nonexisting@example.com"})
            self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)


class SudoTestCase(APITestCase):
    def test_sudo(self):
        user = get_user_model()(username="sudotest", is_staff=True, email="sudotest@example.com", is_superuser=True)
        user.save()
        user2 = get_user_model()(username="sudotest2", email="sudotest2@example.com")
        user2.save()

        self.client.force_authenticate(user)
        req = self.client.post(reverse("sudo"), {"id": user2.id})
        self.assertEqual(req.status_code, HTTP_200_OK)


class GenerateInvitesTestCase(APITestCase):
    def test_response_length(self):
        user = get_user_model()(username="resend-email", is_staff=True, email="tvu@example.com", is_superuser=True)
        user.save()
        self.client.force_authenticate(user=user)
        team = Team.objects.create(owner=user, name=user.username, password="123123")
        response = self.client.post(reverse("generate-invites"), {"amount": 15, "auto_team": team.id, "max_uses": 1})
        self.assertEqual(len(response.data["d"]["invite_codes"]), 15)

    def test_invites_viewset(self):
        user = get_user_model()(username="resend-email", is_staff=True, email="tvu@example.com", is_superuser=True)
        user.save()
        self.client.force_authenticate(user=user)
        self.client.post(reverse("generate-invites"), {"amount": 15, "max_uses": 1})
        response = self.client.get(reverse("invites-list"))
        self.assertEqual(len(response.data["d"]["results"]), 15)


class InviteRequiredRegistrationTestCase(APITestCase):
    def setUp(self):
        RegistrationView.throttle_scope = ""
        config.set("invite_required", True)
        InviteCode(code="test1", max_uses=10).save()
        InviteCode(code="test2", max_uses=1).save()
        InviteCode(code="test3", max_uses=1).save()
        user = get_user_model()(username="invtestadmin", email="invtestadmin@example.org", email_verified=True, is_superuser=True, is_staff=True)
        user.set_password("password")
        user.save()
        self.user = user
        team = Team(name="team", password="password", owner=user)
        team.save()
        self.team = team
        InviteCode(code="test4", max_uses=1, auto_team=team).save()

    def tearDown(self):
        config.set("invite_required", False)

    def test_register_invite_required_missing_invite(self):
        data = {
            "username": "user7",
            "password": "uO7*$E@0ngqL",
            "email": "user7@example.com",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_invite_required_valid(self):
        data = {
            "username": "user8",
            "password": "uO7*$E@0ngqL",
            "email": "user8@example.com",
            "invite": "test1",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_register_invite_required_invalid(self):
        data = {
            "username": "user8",
            "password": "uO7*$E@0ngqL",
            "email": "user8@example.com",
            "invite": "test1---",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_register_invite_required_already_used(self):
        data = {
            "username": "user9",
            "password": "uO7*$E@0ngqL",
            "email": "user9@example.com",
            "invite": "test2",
        }
        response = self.client.post(reverse("register"), data)
        data = {
            "username": "user10",
            "password": "uO7*$E@0ngqL",
            "email": "user10@example.com",
            "invite": "test2",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_register_invite_required_valid_maxing_uses(self):
        data = {
            "username": "user11",
            "password": "uO7*$E@0ngqL",
            "email": "user11@example.com",
            "invite": "test3",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_register_invite_required_auto_team(self):
        data = {
            "username": "user12",
            "password": "uO7*$E@0ngqL",
            "email": "user12@example.com",
            "invite": "test4",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(get_user_model().objects.get(username="user12").team.id, self.team.id)


class LogoutTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="logout-test", email="logout-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user

    def test_logout(self):
        self.client.post(reverse("login"), data={"username": self.user.username, "password": "password", "otp": ""})
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_logout_not_logged_in(self):
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)


class LoginTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="login-test", email="login-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user
        LoginView.throttle_scope = ""

    def test_login(self):
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_login_invalid(self):
        data = {
            "username": "login-test",
            "password": "a",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_missing_data(self):
        data = {
            "username": "login-test",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_login_email_not_verified(self):
        self.user.email_verified = False
        self.user.save()
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    @mock.patch("time.time", side_effect=get_fake_time)
    def test_login_login_closed(self, mock_obj):
        data = {
            "username": "login-test",
            "password": "password",
        }
        config.set("enable_prelogin", False)
        response = self.client.post(reverse("login"), data)
        config.set("enable_prelogin", True)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_inactive(self):
        self.user.is_active = False
        self.user.save()
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.user.is_active = True
        self.user.save()

    def test_login_with_email(self):
        data = {
            "username": "login-test@example.org",
            "password": "password",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_login_wrong_user(self):
        data = {
            "username": "login-",
            "password": "password",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_wrong_password(self):
        data = {
            "username": "login-test",
            "password": "passw",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_malformed(self):
        data = {
            "username": "login-test",
            "otp": "",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_login_2fa_required(self):
        TOTPDevice(user=self.user, verified=True).save()
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)


class Login2FATestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="login-test", email="login-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        TOTPDevice(user=user, verified=True).save()
        self.user = user
        LoginTwoFactorView.throttle_scope = ""

    def test_login_2fa(self):
        secret = TOTPDevice.objects.get(user=self.user).totp_secret
        totp = pyotp.TOTP(secret)
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": totp.now(),
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_login_2fa_invalid(self):
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "123456",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_2fa_without_2fa(self):
        user = get_user_model()(username="login-test-no-2fa", email="login-test-no-2fa@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        data = {"username": "login-test-no-2fa", "password": "password", "tfa": "123456"}
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_2fa_missing(self):
        data = {
            "username": "login-test",
            "password": "password",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_login_2fa_backup_cde(self):
        BackupCode(user=self.user, code="12345678").save()
        data = {
            "username": "login-test",
            "password": "password",
            "tfa": "12345678",
        }
        response = self.client.post(reverse("login-2fa"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)


class TokenTestCase(APITestCase):
    def test_token_str(self):
        user = get_user_model()(username="token-test", email="token-test@example.org")
        user.save()
        tok = Token(key="a" * 40, user=user)
        self.assertEqual(str(tok), "a" * 40)


class TFATestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="2fa-test", email="2fa-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        self.user = user
        AddTwoFactorView.throttle_scope = ""
        VerifyTwoFactorView.throttle_scope = ""

    def test_add_2fa_unauthenticated(self):
        response = self.client.post(reverse("add-2fa"))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
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
        self.assertEqual(response.status_code, HTTP_200_OK)

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
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_remove_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = get_user_model().objects.get(id=self.user.id).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=get_user_model().objects.get(id=self.user.id))
        response = self.client.post(reverse("remove-2fa"), data={"otp": pyotp.TOTP(totp_device.totp_secret).now()})
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_remove_2fa_fail(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = get_user_model().objects.get(id=self.user.id).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=get_user_model().objects.get(id=self.user.id))
        response = self.client.post(reverse("remove-2fa"), data={"otp": "invalid_otp"})
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_remove_2fa_removes_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        totp_device = get_user_model().objects.get(id=self.user.id).totp_device
        totp_device.verified = True
        totp_device.save()
        self.client.force_authenticate(user=get_user_model().objects.get(id=self.user.id))
        response = self.client.post(reverse("remove-2fa"), data={"otp": pyotp.TOTP(totp_device.totp_secret).now()})
        self.assertFalse(get_user_model().objects.get(id=self.user.id).has_2fa())

    def test_remove_2fa_no_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("add-2fa"))
        user = get_user_model().objects.get(id=self.user.id)
        user.totp_device = None
        user.save()
        response = self.client.post(reverse("remove-2fa"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)


class RequestPasswordResetTestCase(APITestCase):
    def setUp(self):
        RequestPasswordResetView.throttle_scope = ""

    def test_password_reset_request_invalid(self):
        response = self.client.post(reverse("request-password-reset"), data={"email": "user10@example.org"})
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_password_reset_request_valid(self):
        with self.settings(MAIL={"SEND_ADDRESS": "no-reply@ractf.co.uk", "SEND_NAME": "RACTF", "SEND": True, "SEND_MODE": "SES"}):
            get_user_model()(username="test-password-rest", email="user10@example.org", email_verified=True).save()
            response = self.client.post(reverse("request-password-reset"), data={"email": "user10@example.org"})
            self.assertEqual(response.status_code, HTTP_200_OK)


class DoPasswordResetTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="pr-test", email="pr-test@example.org")
        user.set_password("password")
        user.email_verified = True
        user.save()
        PasswordResetToken(user=user, token="testtoken").save()
        self.user = user
        DoPasswordResetView.throttle_scope = ""

    def test_password_reset(self):
        data = {
            "uid": self.user.id,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_password_reset_issues_token(self):
        data = {
            "uid": self.user.id,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertTrue("token" in response.data["d"])

    def test_password_reset_bad_token(self):
        data = {
            "uid": self.user.id,
            "token": "abc",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_password_reset_weak_password(self):
        data = {
            "uid": self.user.id,
            "token": "testtoken",
            "password": "password",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_password_reset_login_disabled(self):
        config.set("enable_login", False)
        data = {
            "uid": self.user.id,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        config.set("enable_login", True)
        self.assertFalse("token" in response.data["d"])

    @mock.patch("time.time", side_effect=get_fake_time)
    def test_password_reset_cant_login_yet(self, obj):
        config.set("enable_prelogin", False)
        data = {
            "uid": self.user.id,
            "token": "testtoken",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("do-password-reset"), data)
        config.set("enable_prelogin", True)
        self.assertFalse("token" in response.data["d"])


class VerifyEmailTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="ev-test", email="ev-test@example.org")
        user.set_password("password")
        user.save()
        self.user = user
        VerifyEmailView.throttle_scope = ""

    def test_email_verify(self):
        data = {
            "uid": self.user.id,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_email_verify_invalid(self):
        data = {
            "uid": 123,
            "token": "haha brr",
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_email_verify_nologin(self):
        config.set("enable_login", False)

        data = {
            "uid": self.user.id,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        config.set("enable_login", False)
        self.assertEqual(response.data["d"], "")

    def test_email_verify_twice(self):
        data = {
            "uid": self.user.id,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_email_verify_bad_token(self):
        data = {
            "uid": self.user.id,
            "token": "abc",
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)


class ChangePasswordTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="cp-test", email="cp-test@example.org")
        user.set_password("password")
        user.save()
        self.user = user
        ChangePasswordView.throttle_scope = ""

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "password",
            "password": "uO7*$E@0ngqL",
        }
        response = self.client.post(reverse("change-password"), data)

        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_change_password_weak(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "password",
            "password": "password",
        }
        response = self.client.post(reverse("change-password"), data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_change_password_invalid_old(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "passwordddddddd",
            "password": "password",
        }
        response = self.client.post(reverse("change-password"), data)
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)


class RegerateBackupCodesTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="backupcode-test", email="backupcode-test@example.org")
        user.set_password("password")
        user.save()
        TOTPDevice(user=user, verified=True).save()
        self.user = user
        RegenerateBackupCodesView.throttle_scope = ""

    def test_regenerate_backup_codes_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertEqual(len(response.data["d"]["backup_codes"]), 10)

    def test_regenerate_backup_codes_length(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertEqual(sum([len(x) for x in response.data["d"]["backup_codes"]]), 80)

    def test_regenerate_backup_codes_unique(self):
        self.client.force_authenticate(user=self.user)
        first_response = self.client.post(reverse("regenerate-backup-codes"))
        second_response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertFalse(set(first_response.data["d"]["backup_codes"]) & set(second_response.data["d"]["backup_codes"]))

    def test_regenerate_backup_codes_no_2fa(self):
        user = get_user_model().objects.get(id=self.user.id)
        user.totp_device.delete()
        user.save()
        self.client.force_authenticate(user=get_user_model().objects.get(id=self.user.id))
        response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)


class CreateBotUserTestCase(APITestCase):
    def setUp(self):
        user = get_user_model()(username="bot-test", email="bot-test@example.org", is_staff=True, is_superuser=True)
        user.set_password("password")
        user.save()
        self.user = user
        CreateBotView.throttle_scope = ""

    def test_unauthenticated(self):
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_authenticated_admin(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_authenticated_not_admin(self):
        self.user.is_staff = False
        self.user.is_superuser = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_issues_token(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("create-bot"),
            data={
                "username": "bottest",
                "is_visible": False,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.assertTrue("token" in response.data["d"])
