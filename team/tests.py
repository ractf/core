from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_403_FORBIDDEN, \
    HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST
from rest_framework.test import APITestCase

from team.models import Team


class TeamSetupMixin:
    def setUp(self):
        self.user = get_user_model()(username='team-test', email='team-test@example.org')
        self.user.save()
        self.team = Team(name='team-test', password='abc', description='', owner=self.user)
        self.team.save()
        self.user.team = self.team
        self.user.save()
        self.admin_user = get_user_model()(username='team-test-admin', email='team-test-admin@example.org')
        self.admin_user.is_staff = True
        self.admin_user.save()


class TeamSelfTestCase(TeamSetupMixin, APITestCase):

    def test_team_self(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_team_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.data['password'], 'abc')

    def test_no_team(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.status_code, HTTP_404_NOT_FOUND)

    def test_not_authed(self):
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_update(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(reverse('team-self'), data={'name': 'name-change'})
        self.assertEquals(response.status_code, HTTP_200_OK)
        self.assertEquals(self.team.name, 'name-change')

    def test_update_not_owner(self):
        self.admin_user.team = self.team
        self.admin_user.is_staff = False
        self.admin_user.save()
        self.client.force_authenticate(user=self.admin_user)
        print(self.team.owner == self.admin_user)
        response = self.client.patch(reverse('team-self'), data={'name': 'name-change'})
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)


class CreateTeamTestCase(TeamSetupMixin, APITestCase):

    def test_create_team(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse('team-create'), data={'name': 'test-team', 'password': 'test'})
        self.assertEquals(response.status_code, HTTP_201_CREATED)

    def test_create_team_in_team(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('team-create'), data={'name': 'test-team', 'password': 'test'})
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_team_not_authed(self):
        response = self.client.post(reverse('team-create'), data={'name': 'test-team', 'password': 'test'})
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_create_duplicate_team(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse('team-create'), data={'name': 'team-test', 'password': 'test'})
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)


class JoinTeamTestCase(TeamSetupMixin, APITestCase):

    def test_join_team(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse('team-join'), data={'name': 'team-test', 'password': 'abc'})
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_join_team_duplicate(self):
        self.client.force_authenticate(self.admin_user)
        self.client.post(reverse('team-join'), data={'name': 'team-test', 'password': 'abc'})
        response = self.client.post(reverse('team-join'), data={'name': 'team-test', 'password': 'abc'})
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_not_authed(self):
        response = self.client.post(reverse('team-join'), data={'name': 'team-test', 'password': 'abc'})
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_join_team_team_owner(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('team-join'), data={'name': 'team-test', 'password': 'abc'})
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_join_team_malformed(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse('team-join'), data={'name': 'team-test'})
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)


class TeamViewsetTestCase(TeamSetupMixin, APITestCase):

    def test_visible_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse('team-list'))
        self.assertEquals(len(response.data['results']), 1)

    def test_visible_not_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('team-list'))
        print(response.data)
        self.assertEquals(len(response.data['results']), 0)

    def test_visible_detail_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse('team-detail', kwargs={'pk': self.team.id}))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_visible_detail_not_admin(self):
        self.team.is_visible = False
        self.team.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('team-detail', kwargs={'pk': self.team.id}))
        self.assertEquals(response.status_code, HTTP_404_NOT_FOUND)

    def test_view_password_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse('team-detail', kwargs={'pk': self.team.id}))
        self.assertTrue('password' in response.data)

    def test_view_password_not_admin(self):
        self.admin_user.is_staff = False
        self.admin_user.save()
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse('team-detail', kwargs={'pk': self.team.id}))
        self.assertFalse('password' in response.data)

    def test_view_team(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('team-detail', kwargs={'pk': self.team.id}))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_patch_team(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(reverse('team-detail', kwargs={'pk': self.team.id}), data={'name': 'test'})
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_patch_team_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.patch(reverse('team-detail', kwargs={'pk': self.team.id}), data={'name': 'test'})
        self.assertEquals(response.status_code, HTTP_200_OK)


