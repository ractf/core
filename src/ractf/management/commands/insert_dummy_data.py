from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from challenge.models import Challenge, Category
from hint.models import Hint
from team.models import Team


class Command(BaseCommand):

    def handle(self, *args, **options):
        category = Category(name='test', display_order=0, contained_type='test', description='')
        category.save()
        challenge1 = Challenge(name='test1', category=category, description='a', challenge_type='basic',
                               challenge_metadata={}, flag_type='plaintext', flag_metadata={'flag': 'ractf{a}'},
                               author='dave', score=1000)
        challenge2 = Challenge(name='test2', category=category, description='a', challenge_type='basic',
                               challenge_metadata={}, flag_type='plaintext', flag_metadata={'flag': 'ractf{a}'},
                               author='dave', score=1000)
        challenge3 = Challenge(name='test3', category=category, description='a', challenge_type='basic',
                               challenge_metadata={}, flag_type='plaintext', flag_metadata={'flag': 'ractf{a}'},
                               author='dave', score=1000)
        challenge1.save()
        challenge2.save()
        challenge3.save()
        challenge2.unlocks.add(challenge1)
        challenge2.save()
        hint1 = Hint(name='hint1', challenge=challenge1, text='a', penalty=100)
        hint2 = Hint(name='hint2', challenge=challenge1, text='a', penalty=100)
        hint3 = Hint(name='hint3', challenge=challenge2, text='a', penalty=100)
        hint1.save()
        hint2.save()
        hint3.save()
        user = get_user_model()(username='test', email='challenge-test@example.org')
        user.save()
        team = Team(name='team', password='password', owner=user)
        team.save()
        user.team = team
        user.save()
        user2 = get_user_model()(username='test-2', email='challenge-test-2@example.org')
        user2.team = team
        user2.save()
        user3 = get_user_model()(username='test-3', email='challenge-test-3@example.org')
        user3.save()
        team2 = Team(name='team2', password='password', owner=user3)
        team2.save()
        user3.team = team2
        user3.save()
