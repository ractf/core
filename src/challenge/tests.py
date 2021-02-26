from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED, HTTP_201_CREATED, \
    HTTP_400_BAD_REQUEST
from rest_framework.test import APITestCase

from challenge.models import Category, Challenge, Solve
from config import config
from hint.models import Hint, HintUse
from team.models import Team


class ChallengeSetupMixin:

    def setUp(self):
        category = Category(name='test', display_order=0, contained_type='test', description='')
        category.save()
        challenge1 = Challenge(name='test1', category=category, description='a', challenge_type='basic',
                               challenge_metadata={}, flag_type='plaintext', flag_metadata={'flag': 'ractf{a}'},
                               author='dave', score=1000)
        challenge2 = Challenge(name='test2', category=category, description='a', challenge_type='basic',
                               challenge_metadata={}, flag_type='plaintext', flag_metadata={'flag': 'ractf{a}'},
                               author='dave', score=1000, auto_unlock=True)
        challenge3 = Challenge(name='test3', category=category, description='a', challenge_type='basic',
                               challenge_metadata={}, flag_type='plaintext', flag_metadata={'flag': 'ractf{a}'},
                               author='dave', score=1000, auto_unlock=False)
        challenge1.save()
        challenge2.save()
        challenge3.save()
        challenge1.unlock_requirements = "2"
        challenge1.save()
        hint1 = Hint(name='hint1', challenge=challenge1, text='a', penalty=100)
        hint2 = Hint(name='hint2', challenge=challenge1, text='a', penalty=100)
        hint3 = Hint(name='hint3', challenge=challenge2, text='a', penalty=100)
        hint1.save()
        hint2.save()
        hint3.save()
        user = get_user_model()(username='challenge-test', email='challenge-test@example.org')
        user.save()
        team = Team(name='team', password='password', owner=user)
        team.save()
        user.team = team
        user.save()
        user2 = get_user_model()(username='challenge-test-2', email='challenge-test-2@example.org')
        user2.team = team
        user2.save()
        user3 = get_user_model()(username='challenge-test-3', email='challenge-test-3@example.org')
        user3.save()
        team2 = Team(name='team2', password='password', owner=user3)
        team2.save()
        user3.team = team2
        user3.save()
        self.user = user
        self.user2 = user2
        self.user3 = user3
        self.team = team
        self.team2 = team2
        self.category = category
        self.challenge1 = challenge1
        self.challenge2 = challenge2
        self.challenge3 = challenge3
        self.hint1 = hint1
        self.hint2 = hint2
        self.hint3 = hint3


class ChallengeTestCase(ChallengeSetupMixin, APITestCase):

    def solve_challenge(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'flag': 'ractf{a}',
            'challenge': self.challenge2.id,
        }
        return self.client.post(reverse('submit-flag'), data)

    def test_challenge_solve(self):
        response = self.solve_challenge()
        self.assertEquals(response.status_code, HTTP_200_OK)
        self.assertEquals(response.data['d']['correct'], True)

    def test_challenge_solve_incorrect_flag(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'flag': 'ractf{b}',
            'challenge': self.challenge2.id,
        }
        response = self.client.post(reverse('submit-flag'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)
        self.assertEquals(response.data['d']['correct'], False)

    def test_challenge_double_solve(self):
        self.solve_challenge()
        self.client.force_authenticate(user=self.user2)
        data = {
            'flag': 'ractf{a}',
            'challenge': self.challenge2.id,
        }
        response = self.client.post(reverse('submit-flag'), data)
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_challenge_unlocks(self):
        self.solve_challenge()
        self.challenge1.unlock_requirements = str(self.challenge2.id)
        self.assertTrue(self.challenge1.is_unlocked(get_user_model().objects.get(id=self.user.id)))

    def test_challenge_unlocks_no_team(self):
        user4 = get_user_model()(username='challenge-test-4', email='challenge-test-4@example.org')
        user4.save()
        self.assertFalse(self.challenge1.is_unlocked(user4))

    def test_challenge_unlocks_locked(self):
        self.assertFalse(self.challenge3.is_unlocked(self.user))

    def test_hint_scoring(self):
        HintUse(hint=self.hint3, team=self.team, user=self.user, challenge=self.challenge2).save()
        self.solve_challenge()
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.data['solves'][0]['points'], 900)

    def test_solve_first_blood(self):
        self.solve_challenge()
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.data['solves'][0]['first_blood'], True)

    def test_solve_solved_by_name(self):
        self.solve_challenge()
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.data['solves'][0]['solved_by_name'], 'challenge-test')

    def test_solve_team_name(self):
        self.solve_challenge()
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.data['solves'][0]['team_name'], 'team')

    def test_normal_scoring(self):
        self.solve_challenge()
        response = self.client.get(reverse('team-self'))
        self.assertEquals(response.data['solves'][0]['points'], 1000)

    def test_is_solved(self):
        self.solve_challenge()
        self.assertTrue(self.challenge2.is_solved(user=self.user))

    def test_is_not_solved(self):
        self.assertFalse(self.challenge1.is_solved(user=self.user))

    def test_submission_disabled(self):
        config.set('enable_flag_submission', False)
        response = self.solve_challenge()
        config.set('enable_flag_submission', True)
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_submission_malformed(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'flag': 'ractf{a}',
        }
        response = self.client.post(reverse('submit-flag'), data)
        self.assertEquals(response.status_code, HTTP_400_BAD_REQUEST)

    def test_challenge_score_same_team(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'flag': 'ractf{a}',
            'challenge': self.challenge2.id,
        }
        self.client.post(reverse('submit-flag'), data)
        self.client.force_authenticate(user=self.user2)
        data = {
            'flag': 'ractf{a}',
            'challenge': self.challenge2.id,
        }
        response = self.client.post(reverse('submit-flag'), data)
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_challenge_score_not_first_blood(self):
        self.solve_challenge()
        self.client.force_authenticate(user=self.user3)
        data = {
            'flag': 'ractf{a}',
            'challenge': self.challenge2.id,
        }
        response = self.client.post(reverse('submit-flag'), data)
        self.assertEquals(response.status_code, HTTP_200_OK)
        self.assertFalse(Solve.objects.get(team=self.team2, challenge=self.challenge2).first_blood)

    def test_challenge_solved_unauthed(self):
        self.assertFalse(self.challenge2.is_solved(AnonymousUser()))

    def test_challenge_unlocked_unauthed(self):
        self.assertFalse(self.challenge2.is_unlocked(AnonymousUser()))

    def test_challenge_solved_no_team(self):
        user4 = get_user_model()(username='challenge-test-4', email='challenge-test-4@example.org')
        user4.save()
        self.assertFalse(self.challenge2.is_solved(user4))


class CategoryViewsetTestCase(ChallengeSetupMixin, APITestCase):

    def test_category_list_unauthenticated_permission(self):
        response = self.client.get(reverse('categories-list'))
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_category_list_authenticated_permission(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('categories-list'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_category_list_unauthenticated_content(self):
        response = self.client.get(reverse('categories-list'))
        self.assertFalse(response.data['s'])
        self.assertEquals(response.data['m'], 'not_authenticated')
        self.assertEquals(response.data['d'], '')

    def test_category_list_authenticated_content(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('categories-list'))
        self.assertEquals(len(response.data['d']), 1)
        self.assertEquals(len(response.data['d'][0]['challenges']), 3)

    def test_category_list_challenge_redacting(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('categories-list'))
        self.assertFalse('description' in response.data['d'][0]['challenges'][0])

    def test_category_list_challenge_redacting_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('categories-list'))
        self.assertTrue('description' in response.data['d'][0]['challenges'][0])

    def test_category_list_challenge_unlocked_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('categories-list'))
        self.assertFalse(response.data['d'][0]['challenges'][0]['unlocked'])

    def test_category_create(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('categories-list'), data={
            'name': 'test-category-2',
            'contained_type': 'test',
            'description': 'test',
        })
        self.assertTrue(response.status_code, HTTP_200_OK)

    def test_category_create_unauthorized(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('categories-list'), data={
            'name': 'test-category-2',
            'contained_type': 'test',
            'description': 'test',
        })
        self.assertTrue(response.status_code, HTTP_403_FORBIDDEN)


class ChallengeViewsetTestCase(ChallengeSetupMixin, APITestCase):
    
    def test_challenge_list_unauthenticated_permission(self):
        response = self.client.get(reverse('challenges-list'))
        self.assertEquals(response.status_code, HTTP_401_UNAUTHORIZED)

    def test_challenge_list_authenticated_permission(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-list'))
        self.assertEquals(response.status_code, HTTP_200_OK)

    def test_challenge_list_unauthenticated_content(self):
        response = self.client.get(reverse('challenges-list'))
        self.assertFalse(response.data['s'])
        self.assertEquals(response.data['m'], 'not_authenticated')
        self.assertEquals(response.data['d'], '')

    def test_challenge_list_authenticated_content(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-list'))
        self.assertEquals(len(response.data), 3)

    def test_challenge_list_challenge_redacting(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-list'))
        self.assertFalse('description' in response.data[0])

    def test_challenge_list_challenge_redacting_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-list'))
        self.assertTrue('description' in response.data[0])

    def test_challenge_list_challenge_unlocked_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-list'))
        self.assertFalse(response.data[0]['unlocked'])

    def test_single_challenge_redacting(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-detail', kwargs={'pk': self.challenge1.id}))
        self.assertFalse('description' in response.data)

    def test_single_challenge_admin_redacting(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-detail', kwargs={'pk': self.challenge1.id}))
        self.assertTrue('description' in response.data)

    def test_admin_unlocking(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('challenges-detail', kwargs={'pk': self.challenge1.id}))
        self.assertFalse(response.data['unlocked'])

    def test_user_post_detail(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('challenges-detail', kwargs={'pk': self.challenge1.id}))
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_user_post_list(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('challenges-list'))
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

    def test_create_challenge(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('challenges-list'), data={
            'name': 'test4', 'category': self.category.id, 'description': 'abc',
            'challenge_type': 'test', 'challenge_metadata': {}, 'flag_type': 'plaintext',
            'author': 'dave', 'auto_unlock': True, 'score': 1000, 'unlock_requirements': "", 'flag_metadata': {},
            'tags': [],
        }, format='json')
        self.assertEquals(response.status_code, HTTP_201_CREATED)

    def test_create_challenge_unauthorized(self):
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('challenges-list'), data={
            'name': 'test4', 'category': self.category.id, 'description': 'abc',
            'challenge_type': 'test', 'challenge_metadata': {}, 'flag_type': 'plaintext',
            'author': 'dave', 'auto_unlock': True, 'score': 1000, 'unlock_requirements': "a", 'flag_metadata': {}
        }, format='json')
        self.assertEquals(response.status_code, HTTP_403_FORBIDDEN)

