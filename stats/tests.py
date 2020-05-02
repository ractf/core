from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase


class CountdownTestCase(APITestCase):

    def test_unauthed(self):
        response = self.client.get(reverse('countdown'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_authed(self):
        user = get_user_model()(username='countdown-test', email='countdown-test@example.org')
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse('countdown'))
        self.assertEquals(response.status_code, HTTP_200_OK)


class StatsTestCase(APITestCase):

    def test_unauthed(self):
        response = self.client.get(reverse('stats'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_authed(self):
        user = get_user_model()(username='stats-test', email='stats-test@example.org')
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse('stats'))
        self.assertEquals(response.status_code, HTTP_200_OK)


class CommitTestCase(APITestCase):

    def test_unauthed(self):
        response = self.client.get(reverse('version'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_authed(self):
        user = get_user_model()(username='commit-test', email='commit-test@example.org')
        user.save()
        self.client.force_authenticate(user)
        response = self.client.get(reverse('version'))
        self.assertEquals(response.status_code, HTTP_200_OK)
