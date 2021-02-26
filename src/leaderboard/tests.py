from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from challenge.models import Score
from leaderboard.views import UserListView, TeamListView, GraphView
from team.models import Team


def populate():
    for i in range(15):
        user = get_user_model()(username=f'scorelist-test{i}', email=f'scorelist-test{i}@example.org', is_visible=True)
        user.save()
        team = Team(name=f'scorelist-test{i}', password=f'scorelist-test{i}', owner=user, is_visible=True)
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
        self.assertTrue('user' in response.data['d'])
        self.assertTrue('team' in response.data['d'])

    def test_list_size(self):
        populate()
        response = self.client.get(reverse('leaderboard-graph'))
        print(response.data)
        self.assertEquals(len(response.data['d']['user']), 10)
        self.assertEquals(len(response.data['d']['team']), 10)

    def test_list_sorting(self):
        populate()
        response = self.client.get(reverse('leaderboard-graph'))
        print(response.data)
        self.assertEquals(response.data['d']['user'][0]['points'], 1400)
        self.assertEquals(response.data['d']['team'][0]['points'], 1400)


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
        print(Score.objects.all())
        response = self.client.get(reverse('leaderboard-user'))
        print(response.content)
        self.assertEquals(len(response.data['d']['results']), 15)

    def test_order(self):
        populate()
        response = self.client.get(reverse('leaderboard-user'))
        points = [x['leaderboard_points'] for x in response.data['d']['results']]
        self.assertEquals(points, sorted(points, reverse=True))


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
        self.assertEquals(len(response.data["d"]["results"]), 15)

    def test_order(self):
        populate()
        response = self.client.get(reverse('leaderboard-team'))
        print(response.data)
        points = [x['leaderboard_points'] for x in response.data['d']['results']]
        self.assertEquals(points, sorted(points, reverse=True))
