from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication import views
from authentication.models import InviteCode, TOTPDevice
from authentication.tests import utils
from config import config
from member.models import Member
from team.models import Team


class RegisterTestCase(APITestCase):
    def setUp(self):
        views.RegistrationView.throttle_scope = ""

    def test_register(self):
        data = {
            "username": "user1",
            "password": "uO7*$E@0ngqL",
            "email": "user@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_with_mail(self):
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
        data = {
            "username": "user2",
            "password": "password",
            "email": "user2@example.org",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
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
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6@example.org",
        }
        self.client.post(reverse("register"), data)
        self.assertTrue(Member.objects.filter(username=data["username"]).first().is_staff)

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
        self.assertFalse(Member.objects.filter(username=data["username"]).first().is_staff)

    def test_register_malformed(self):
        data = {
            "username": "user6",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email(self):
        data = {
            "username": "user6",
            "password": "uO7*$E@0ngqL",
            "email": "user6",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_teams_disabled(self):
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
    def test_email_resend(self):
        with self.settings(RATELIMIT_ENABLE=False):
            user = Member(username="test_verify_user", email_verified=False, email="tvu@example.com")
            user.save()
            response = self.client.post(reverse("resend-email"), {"email": "tvu@example.com"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_already_verified_email_resend(self):
        with self.settings(RATELIMIT_ENABLE=False):
            user = Member(username="resend-email", email_verified=True, email="tvu@example.com")
            user.save()
            response = self.client.post(reverse("resend-email"), {"email": "tvu@example.com"})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_existing_email_resend(self):
        with self.settings(RATELIMIT_ENABLE=False):
            response = self.client.post(reverse("resend-email"), {"email": "nonexisting@example.com"})
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class VerifyEmailTestCase(APITestCase):
    def setUp(self):
        user = Member(username="ev-test", email="ev-test@example.org")
        user.set_password("password")
        user.save()
        self.user = user
        views.VerifyEmailView.throttle_scope = ""

    def test_email_verify(self):
        data = {
            "uid": self.user.pk,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_verify_invalid(self):
        data = {
            "uid": 123,
            "token": "haha brr",
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_email_verify_nologin(self):
        config.set("enable_login", False)

        data = {
            "uid": self.user.pk,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        config.set("enable_login", False)
        self.assertEqual(response.data["d"], "")

    def test_email_verify_twice(self):
        data = {
            "uid": self.user.pk,
            "token": self.user.email_token,
        }
        response = self.client.post(reverse("verify-email"), data)
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_verify_bad_token(self):
        data = {
            "uid": self.user.pk,
            "token": "abc",
        }
        response = self.client.post(reverse("verify-email"), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InviteRequiredRegistrationTestCase(APITestCase):
    def setUp(self):
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
        config.set("invite_required", False)

    def test_register_invite_required_missing_invite(self):
        data = {
            "username": "user7",
            "password": "uO7*$E@0ngqL",
            "email": "user7@example.com",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invite_required_valid(self):
        data = {
            "username": "user8",
            "password": "uO7*$E@0ngqL",
            "email": "user8@example.com",
            "invite": "test1",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_invite_required_invalid(self):
        data = {
            "username": "user8",
            "password": "uO7*$E@0ngqL",
            "email": "user8@example.com",
            "invite": "test1---",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_invite_required_valid_maxing_uses(self):
        data = {
            "username": "user11",
            "password": "uO7*$E@0ngqL",
            "email": "user11@example.com",
            "invite": "test3",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_invite_required_auto_team(self):
        data = {
            "username": "user12",
            "password": "uO7*$E@0ngqL",
            "email": "user12@example.com",
            "invite": "test4",
        }
        self.client.post(reverse("register"), data)
        self.assertEqual(Member.objects.get(username="user12").team.pk, self.team.pk)


class RegenerateBackupCodesTestCase(APITestCase):
    def setUp(self):
        user = Member(username="backupcode-test", email="backupcode-test@example.org")
        user.set_password("password")
        user.save()
        TOTPDevice(user=user, verified=True).save()
        self.user = user
        views.RegenerateBackupCodesView.throttle_scope = ""

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
        user = Member.objects.get(id=self.user.pk)
        user.totp_device.delete()
        user.save()
        self.client.force_authenticate(user=Member.objects.get(id=self.user.pk))
        response = self.client.post(reverse("regenerate-backup-codes"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
