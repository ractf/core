import random

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from challenge.models import Challenge, Category, Score, Solve
from team.models import Team


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('Creating 10 categories...')
        for i in range(10):
            category = Category(name='category-' + str(i), display_order=i, contained_type='test',
                                description='Category ' + str(i))
            category.save()

        print('Creating 100 challenges for each category...')
        for i in range(10):
            category = Category.objects.get(name='category-' + str(i))
            for j in range(50):
                challenge = Challenge(name='cat-' + str(i) + '-chal-' + str(j), category=category,
                                      description='An example challenge ' + str(j),
                                      flag_metadata={'flag': f'ractf{{{j}}}'}, author='dave', auto_unlock=True, score=j,
                                      challenge_metadata={})
                challenge.save()
            for j in range(50, 100, 2):
                challenge = Challenge(name='cat-' + str(i) + '-chal-' + str(j), category=category,
                                      description='An example challenge ' + str(j),
                                      flag_metadata={'flag': f'ractf{{{j}}}'}, author='dave', auto_unlock=True,
                                      score=j, challenge_metadata={})
                challenge2 = Challenge(name='cat-' + str(i) + '-chal-' + str(j + 1), category=category,
                                       description='An example challenge ' + str(j + 1),
                                       flag_metadata={'flag': f'ractf{{{j + 1}}}'}, author='dave', auto_unlock=False,
                                       score=j, challenge_metadata={})
                challenge2.save()
                challenge.save()
                challenge.unlocks.add(challenge2)

        print('Creating 20000 users with 10000 teams with 100 solves per team...')
        for i in range(10000):
            user = get_user_model()(username='user-' + str(i), email='user-' + str(i) + '@example.org')
            user.save()
            team = Team(name='team-' + str(i), password='password', owner=user)
            team.save()
            user2 = get_user_model()(username='user-' + str(i) + '-second', email='user-' + str(i) + '-second@example.org',
                                     team=team)
            user2.save()
            for j in range(50):
                challenge = Category.objects.get(name='category-' + str(j % 5))\
                    .category_challenges.get(name='cat-' + str(j % 5) + '-chal-' + str(j))
                points = random.randint(0, 1000)
                score = Score(team=team, reason='challenge', points=points, penalty=0, leaderboard=True)
                score.save()
                solve = Solve(team=team, solved_by=user, challenge=challenge, first_blood=challenge.first_blood is None,
                              flag='ractf{}', score=score, correct=True)
                solve.save()
                user.points += points
                team.points += points
                user.leaderboard_points += points
                team.leaderboard_points += points
            for j in range(50):
                challenge = Category.objects.get(name='category-' + str(j % 5 + 5))\
                    .category_challenges.get(name='cat-' + str(j % 5 + 5) + '-chal-' + str(j))
                points = random.randint(0, 1000)
                score = Score(team=team, reason='challenge', points=points, penalty=0, leaderboard=True)
                score.save()
                solve = Solve(team=team, solved_by=user2, challenge=challenge,
                              first_blood=challenge.first_blood is None, flag='ractf{}', score=score, correct=True)
                solve.save()
                user2.points += points
                team.points += points
                user.leaderboard_points += points
                team.leaderboard_points += points

