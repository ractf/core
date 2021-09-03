"""Tests for registration related authentication api endpoints."""

from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication import views
from authentication.models import InviteCode, TOTPDevice
from authentication.tests import utils
from config import config
from member.models import Member
from teams.models import Team


class RegisterTestCase(APITestCase):
    """Tests for the register endpoint."""

    def setUp(self):
        """Remove the ratelimit."""
        views.RegistrationView.throttle_scope = ""

    def test_register(self):
        """Registering a user should return 201."""
        data = {
            "username": "user1",
            "password": "uO7*$E@0ngqL",
            "email": "user@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_with_mail(self):
        """Registering a user with mail enabled should return True."""
        with self.settings(
            MAIL={"SEND_ADDRESS": "no-reply@ractf.co.uk", "SEND_NAME": "RACTF", "SEND": True, "SEND_MODE": "SES"}
        ):
            data = {
                "username": "user1",
                "password": "uO7*$E@0ngqL",
                "email": "user@example.org",
            }
            response = self.client.post(reverse("register"), data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_weak_password(self):
        """Registering with a weak password should return 400."""
        data = {
            "username": "user2",
            "password": "password",
            "email": "user2@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        """Registering a taken username should return 400."""
        data = {
            "username": "user3",
            "password": "uO7*$E@0ngqL",
            "email": "user3@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = {
            "username": "user3",
            "password": "uO7*$E@0ngqL",
            "email": "user4@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Registering a taken email should return 400."""
        data = {
            "username": "user4",
            "password": "uO7*$E@0ngqL",
            "email": "user4@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = {
            "username": "user5",
            "password": "uO7*$E@0ngqL",
            "email": "user4@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch("time.time", side_effect=utils.get_fake_time)
    def test_register_closed(self, mock_obj):
        """Registering when registration is closed should return 403."""
        config.set("enable_prelogin", False)
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        config.set("enable_prelogin", True)

    def test_register_admin(self):
        """The first registered user should be staff."""
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6@example.org",
        }
        self.client.post(reverse("register"), data)
        self.assertTrue(Member.objects.filter(username=data["username"]).first().is_staff)

    def test_register_second(self):
        """Users after the first registered user should not automatically be staff."""
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
        self.assertFalse(Member.objects.filter(username=data["username"]).first().is_staff)

    def test_register_malformed(self):
        """A malformed registration should return 400."""
        data = {
            "username": "user6",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email(self):
        """Registering with an invalid email should return 400."""
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_teams_disabled(self):
        """Registering with teams disabled should automatically create a new team."""
        config.set("enable_teams", False)
        data = {
            "username": "user10",
            "password": "uO7*$E@0ngqL",
            "email": "user10@example.com",
        }
        response = self.client.post(reverse("register"), data)
        config.set("enable_teams", True)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Member.objects.get(username="user10").team.name, "user10")


class EmailResendTestCase(APITestCase):
    """Tests for resending email verification."""

    def test_email_resend(self):
        """Resending a verification email should always return 200."""
        with self.settings(RATELIMIT_ENABLE=False):
            user = Member(username="test_verify_user", email_verified=False, email="tvu@example.com")
            user.save()
            response = self.client.post(reverse("resend-email"), {"email": "tvu@example.com"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_already_verified_email_resend(self):
        """Resending a verification email should always return 200."""
        with self.settings(RATELIMIT_ENABLE=False):
            user = Member(username="resend-email", email_verified=True, email="tvu@example.com")
            user.save()
            response = self.client.post(reverse("resend-email"), {"email": "tvu@example.com"})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_existing_email_resend(self):
        """Resending a verification email should always return 200."""
        with self.settings(RATELIMIT_ENABLE=False):
            response = self.client.post(reverse("resend-email"), {"email": "nonexisting@example.com"})
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class VerifyEmailTestCase(APITestCase):
    """Tests for verifying a users email."""

    def setUp(self):
        """Create a test user and remove the ratelimits."""
        user = Member(username="ev-test", email="ev-test@example.org")
        user.set_password("password")
        user.save()
        self.user = user
        views.VerifyEmailView.throttle_scope = ""

    def test_email_verify(self):
        """Verifying an email should return 200."""
        data = {
            "uid": self.user.pk,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_verify_invalid(self):
        """Verifying email with an invalid user should return 404."""
        data = {
            "uid": 123,
            "token": "haha brr",
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_email_verify_nologin(self):
        """Verifying email when login is disabled should not issue a token."""
        config.set("enable_login", False)

        data = {
            "uid": self.user.pk,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        config.set("enable_login", False)
        self.assertEqual(response.data["d"], "")

    def test_email_verify_twice(self):
        """Verifying an already verified email should return 400."""
        data = {
            "uid": self.user.pk,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_verify_bad_token(self):
        """Verifying email with an invalid token should return 404."""
        data = {
            "uid": self.user.pk,
            "token": "abc",
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InviteRequiredRegistrationTestCase(APITestCase):
    """Tests for registration when invites are required."""

    def setUp(self):
        """Create some invites, users, teams for testing."""
        views.RegistrationView.throttle_scope = ""
        config.set("invite_required", True)
        InviteCode(code="test1", max_uses=10).save()
        InviteCode(code="test2", max_uses=1).save()
        InviteCode(code="test3", max_uses=1).save()
        user = Member(
            username="invtestadmin",
            email="invtestadmin@example.org",
            email_verified=True,
            is_superuser=True,
            is_staff=True,
        )
        user.set_password("password")
        user.save()
        self.user = user
        team = Team(name="team", password="password", owner=user)
        team.save()
        self.team = team
        InviteCode(code="test4", max_uses=1, auto_team=team).save()

    def tearDown(self):
        """Undo changes to config."""
        config.set("invite_required", False)

    def test_register_invite_required_missing_invite(self):
        """Registering without an invite should return 400."""
        data = {
            "username": "user7",
            "password": "uO7*$E@0ngqL",
            "email": "user7@example.com",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invite_required_valid(self):
        """Registering with a valid invite should return 201."""
        data = {
            "username": "user8",
            "password": "uO7*$E@0ngqL",
            "email": "user8@example.com",
            "invite": "test1",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_invite_required_invalid(self):
        """Registering with an invalid invite should return 403."""
        data = {
            "username": "user8",
            "password": "uO7*$E@0ngqL",
            "email": "user8@example.com",
            "invite": "test1---",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_invite_required_already_used(self):
        """Registering with an already used invite should return 403."""
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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_invite_required_valid_maxing_uses(self):
        """Registering when the invite is one use off max should return 201."""
        data = {
            "username": "user11",
            "password": "uO7*$E@0ngqL",
            "email": "user11@example.com",
            "invite": "test3",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_invite_required_auto_team(self):
        """Registering with an auto team invite should add the user to that team."""
        data = {
            "username": "user12",
            "password": "uO7*$E@0ngqL",
            "email": "user12@example.com",
            "invite": "test4",
        }
        self.client.post(reverse("register"), data)
        self.assertEqual(Member.objects.get(username="user12").team.pk, self.team.pk)


class RegenerateBackupCodesTestCase(APITestCase):
    """Tests for regenerating backup codes."""

    def setUp(self):
        """Create a user and totp device for testing, remove the ratelimit."""
        user = Member(username="backupcode-test", email="backupcode-test@example.org")
        user.set_password("password")
        user.save()
        TOTPDevice(user=user, verified=True).save()
        self.user = user
        views.RegenerateBackupCodesView.throttle_scope = ""

    def test_regenerate_backup_codes_count(self):
        """Test the correct amount of backup codes are regenerated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertEqual(len(response.data["d"]["backup_codes"]), 10)

    def test_regenerate_backup_codes_length(self):
        """Backup codes should be 8 characters each."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertEqual(sum([len(x) for x in response.data["d"]["backup_codes"]]), 80)

    def test_regenerate_backup_codes_unique(self):
        """Each backup code should be unique."""
        self.client.force_authenticate(user=self.user)
        first_response = self.client.post(reverse("regenerate-backup-codes"))
        second_response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertFalse(set(first_response.data["d"]["backup_codes"]) & set(second_response.data["d"]["backup_codes"]))

    def test_regenerate_backup_codes_no_2fa(self):
        """Backup codes should not be able to be generated if 2fa is disabled."""
        user = Member.objects.get(id=self.user.pk)
        user.totp_device.delete()
        user.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
