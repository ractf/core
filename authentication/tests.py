from unittest import mock

import pyotp
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_403_FORBIDDEN, \
    HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED
from rest_framework.test import APITestCase

from authentication.views import VerifyEmailView, DoPasswordResetView, AddTwoFactorView, VerifyTwoFactorView, LoginView, \
    RegistrationView, ChangePasswordView
from member.models import TOTPStatus


def get_fake_time():
    return 0


class RegisterTestCase(APITestCase):

    def setUp(self):
        RegistrationView.throttle_scope = ''

    def test_register(self):
        data = {
            'username': 'user1',
            'password': 'uO7*$E@0ngqL',
            'email': 'user@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEquals(response.status_code, HTTP_201_CREATED)

    def test_register_weak_password(self):
        data = {
            'username': 'user2',
            'password': 'password',
            'email': 'user2@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        data = {
            'username': 'user3',
            'password': 'uO7*$E@0ngqL',
            'email': 'user3@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEquals(response.status_code, HTTP_201_CREATED)
        data = {
            'username': 'user3',
            'password': 'uO7*$E@0ngqL',
            'email': 'user4@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        data = {
            'username': 'user4',
            'password': 'uO7*$E@0ngqL',
            'email': 'user4@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEquals(response.status_code, HTTP_201_CREATED)
        data = {
            'username': 'user5',
            'password': 'uO7*$E@0ngqL',
            'email': 'user4@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    @mock.patch('time.time', side_effect=get_fake_time)
    def test_register_closed(self, mock_obj):
        data = {
            'username': 'user6',
            'password': 'uO7*$E@0ngqL',
            'email': 'user6@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    def test_register_admin(self):
        data = {
            'username': 'user6',
            'password': 'uO7*$E@0ngqL',
            'email': 'user6@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertTrue(get_user_model().objects.filter(id=response.data['id']).first().is_staff)

    def test_register_second(self):
        data = {
            'username': 'user6',
            'password': 'uO7*$E@0ngqL',
            'email': 'user6@example.org',
        }
        self.client.post(reverse('register'), data)
        data = {
            'username': 'user7',
            'password': 'uO7*$E@0ngqL',
            'email': 'user7@example.org',
        }
        response = self.client.post(reverse('register'), data)
        self.assertFalse(get_user_model().objects.filter(id=response.data['id']).first().is_staff)


class LogoutTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='logout-test', email='logout-test@example.org')
        user.set_password('password')
        user.email_verified = True
        user.save()
        self.user = user

    def test_logout(self):
        self.client.post(reverse('login'), data={'username': self.user.username, 'password': 'password', 'otp': ''})
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('logout'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_logout_not_logged_in(self):
        response = self.client.post(reverse('logout'))
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)


class LoginTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='login-test', email='login-test@example.org')
        user.set_password('password')
        user.email_verified = True
        user.save()
        self.user = user
        LoginView.throttle_scope = ''

    def test_login(self):
        data = {
            'username': 'login-test',
            'password': 'password',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_login_invalid(self):
        data = {
            'username': 'login-test',
            'password': 'a',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_missing_data(self):
        data = {
            'username': 'login-test',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    def test_login_2fa(self):
        secret = pyotp.random_base32()
        self.user.totp_secret = secret
        self.user.totp_status = TOTPStatus.ENABLED
        self.user.save()
        totp = pyotp.TOTP(secret)
        data = {
            'username': 'login-test',
            'password': 'password',
            'otp': totp.now(),
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)
        self.user.totp_status = TOTPStatus.DISABLED
        self.user.save()

    def test_login_2fa_invalid(self):
        secret = pyotp.random_base32()
        self.user.totp_secret = secret
        self.user.totp_status = TOTPStatus.ENABLED
        self.user.save()
        data = {
            'username': 'login-test',
            'password': 'password',
            'otp': '123456',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)
        self.user.totp_status = TOTPStatus.DISABLED
        self.user.save()

    def test_login_2fa_missing(self):
        secret = pyotp.random_base32()
        self.user.totp_secret = secret
        self.user.totp_status = TOTPStatus.ENABLED
        self.user.save()
        data = {
            'username': 'login-test',
            'password': 'password',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)
        self.user.totp_status = TOTPStatus.DISABLED
        self.user.save()

    def test_login_email_not_verified(self):
        self.user.email_verified = False
        self.user.save()
        data = {
            'username': 'login-test',
            'password': 'password',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    @mock.patch('time.time', side_effect=get_fake_time)
    def test_login_login_closed(self, mock_obj):
        data = {
            'username': 'login-test',
            'password': 'password',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_inactive(self):
        self.user.is_active = False
        self.user.save()
        data = {
            'username': 'login-test',
            'password': 'password',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)
        self.user.is_active = True
        self.user.save()

    def test_login_with_email(self):
        data = {
            'username': 'login-test@example.org',
            'password': 'password',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_login_wrong_user(self):
        data = {
            'username': 'login-',
            'password': 'password',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_wrong_password(self):
        data = {
            'username': 'login-test',
            'password': 'passw',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_login_malformed(self):
        data = {
            'username': 'login-test',
            'otp': '',
        }
        response = self.client.post(reverse('login'), data)
        print(response.data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)


class TFATestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='2fa-test', email='2fa-test@example.org')
        user.set_password('password')
        user.email_verified = True
        user.save()
        self.user = user
        AddTwoFactorView.throttle_scope = ''
        VerifyTwoFactorView.throttle_scope = ''

    def test_add_2fa_unauthenticated(self):
        self.client.post(reverse('add-2fa'))
        self.assertEquals(self.user.totp_status, TOTPStatus.DISABLED)

    def test_add_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse('add-2fa'))
        self.assertEquals(self.user.totp_status, TOTPStatus.VERIFYING)
        self.assertNotEquals(self.user.totp_secret, None)

    def test_verify_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse('add-2fa'))
        secret = self.user.totp_secret
        totp = pyotp.TOTP(secret)
        self.client.post(reverse('verify-2fa'), data={'otp': totp.now()})
        self.assertEquals(self.user.totp_status, TOTPStatus.ENABLED)

    def test_verify_2fa_invalid(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse('add-2fa'))
        self.client.post(reverse('verify-2fa'), data={'otp': '123456'})
        self.assertEquals(self.user.totp_status, TOTPStatus.VERIFYING)

    def test_add_2fa_with_2fa(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse('add-2fa'))
        secret = self.user.totp_secret
        totp = pyotp.TOTP(secret)
        self.client.post(reverse('verify-2fa'), data={'otp': totp.now()})
        response = self.client.post(reverse('add-2fa'))
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)


class RequestPasswordResetTestCase(APITestCase):

    def test_password_reset_request_invalid(self):
        response = self.client.post(reverse('request-password-reset'), data={'email': 'user10@example.org'})
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_password_reset_request_valid(self):
        get_user_model()(username='test-password-rest', email='user10@example.org').save()
        response = self.client.post(reverse('request-password-reset'), data={'email': 'user10@example.org'})
        self.assertEquals(response.status_code, HTTP_200_OK)


class DoPasswordResetTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='pr-test', email='pr-test@example.org')
        user.set_password('password')
        user.email_verified = True
        user.save()
        self.user = user
        DoPasswordResetView.throttle_scope = ''

    def test_password_reset(self):
        data = {
            'uid': self.user.id,
            'token': self.user.password_reset_token,
            'password': 'uO7*$E@0ngqL',
        }
        response = self.client.post(reverse('do-password-reset'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_password_reset_bad_token(self):
        data = {
            'uid': self.user.id,
            'token': 'abc',
            'password': 'uO7*$E@0ngqL',
        }
        response = self.client.post(reverse('do-password-reset'), data)
        self.assertEquals(response.status_code, HTTP_404_NOT_FOUND)

    def test_password_reset_weak_password(self):
        data = {
            'uid': self.user.id,
            'token': self.user.password_reset_token,
            'password': 'password',
        }
        response = self.client.post(reverse('do-password-reset'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)


class VerifyEmailTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='ev-test', email='ev-test@example.org')
        user.set_password('password')
        user.save()
        self.user = user
        VerifyEmailView.throttle_scope = ''

    def test_email_verify(self):
        data = {
            'uid': self.user.id,
            'token': self.user.email_token,
        }
        response = self.client.post(reverse('verify-email'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_email_verify_twice(self):
        data = {
            'uid': self.user.id,
            'token': self.user.email_token,
        }
        response = self.client.post(reverse('verify-email'), data)
        response = self.client.post(reverse('verify-email'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    def test_email_verify_bad_token(self):
        data = {
            'uid': self.user.id,
            'token': 'abc',
        }
        response = self.client.post(reverse('verify-email'), data)
        self.assertEquals(response.status_code, HTTP_404_NOT_FOUND)


class ChangePasswordTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='cp-test', email='cp-test@example.org')
        user.set_password('password')
        user.save()
        self.user = user
        ChangePasswordView.throttle_scope = ''

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'password': 'uO7*$E@0ngqL',
        }
        response = self.client.post(reverse('change-password'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_change_password_weak(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'password': 'password',
        }
        response = self.client.post(reverse('change-password'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)
