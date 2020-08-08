from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from challenge.models import Score
from leaderboard.views import UserListView, TeamListView, GraphView
from team.models import Team


def populate():
    for i in range(15):
        user = get_user_model()(username=f'scorelist-test{i}', email=f'scorelist-test{i}@example.org')
        user.save()
        team = Team(name=f'scorelist-test{i}', password=f'scorelist-test{i}', owner=user)
        team.points = i * 100
        team.leaderboard_points = i * 100
        team.save()
        user.team = team
        user.points = i * 100
        user.leaderboard_points = i * 100
        user.save()
        Score(team=team, user=user, reason='test', points=i * 100).save()


class ScoreListTestCase(APITestCase):

    def setUp(self):
        GraphView.throttle_scope = ''
        user = get_user_model()(username='scorelist-test', email='scorelist-test@example.org')
        user.save()
        self.user = user

    def test_unauthed_access(self):
        response = self.client.get(reverse('leaderboard-graph'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_authed_access(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('leaderboard-graph'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_format(self):
        response = self.client.get(reverse('leaderboard-graph'))
        self.assertTrue('user' in response.data)
        self.assertTrue('team' in response.data)

    def test_list_size(self):
        populate()
        response = self.client.get(reverse('leaderboard-graph'))
        print(response.data)
        self.assertEquals(len(response.data['user']), 10)
        self.assertEquals(len(response.data['team']), 10)

    def test_list_sorting(self):
        populate()
        response = self.client.get(reverse('leaderboard-graph'))
        print(response.data)
        self.assertEquals(response.data['user'][-1]['points'], 1400)
        self.assertEquals(response.data['team'][-1]['points'], 1400)


class UserListTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='userlist-test', email='userlist-test@example.org')
        user.save()
        self.user = user
        UserListView.throttle_scope = None

    def test_unauthed(self):
        response = self.client.get(reverse('leaderboard-user'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_authed(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('leaderboard-user'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_length(self):
        populate()
        response = self.client.get(reverse('leaderboard-user'))
        self.assertEquals(len(response.data['results']), 16)

    def test_order(self):
        populate()
        response = self.client.get(reverse('leaderboard-user'))
        self.assertTrue(response.data['results'][0]['leaderboard_points']
                        > response.data['results'][1]['leaderboard_points'])


class TeamListTestCase(APITestCase):

    def setUp(self):
        user = get_user_model()(username='userlist-test', email='userlist-test@example.org')
        user.save()
        self.user = user
        TeamListView.throttle_scope = None

    def test_unauthed(self):
        response = self.client.get(reverse('leaderboard-team'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_authed(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('leaderboard-team'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_length(self):
        populate()
        response = self.client.get(reverse('leaderboard-team'))
        self.assertEquals(len(response.data['results']), 15)

    def test_order(self):
        populate()
        response = self.client.get(reverse('leaderboard-team'))
        self.assertTrue(response.data['results'][0]['leaderboard_points']
                        > response.data['results'][1]['leaderboard_points'])
