import random
import time

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.db import transaction

from challenge.models import Challenge, Category, Score, Solve
from team.models import Team


def timed_log(call, msg):
    before_call = time.time()
    print(msg, end=" ", flush=True)
    call()
    print("Done (" + str(time.time() - before_call) + "s)")


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('Creating 10 categories...')
        for i in range(10):
            category = Category(name='category-' + str(i), display_order=i, contained_type='test',
                                description='Category ' + str(i))
            category.save()

        print('Creating 100 challenges for each category...')

        def random_rpn_op(depth=0):
            depth += 1

            if depth > 4 or (random.randint(1, 4) < 3 and depth > 1):
                return str(random.randint(1, 1000))

            if random.randint(1, 2) == 1:
                return f"{random_rpn_op(depth)} {random_rpn_op(depth)} OR"
            else:
                return f"{random_rpn_op(depth)} {random_rpn_op(depth)} AND"

        for i in range(10):
            category = Category.objects.get(name='category-' + str(i))
            for j in range(100):
                auto_unlock = (random.randint(1, 2) == 1)
                challenge = Challenge(name='cat-' + str(i) + '-chal-' + str(j), category=category,
                                      description='An example challenge ' + str(j),
                                      flag_metadata={'flag': f'ractf{{{j}}}'}, author='dave', auto_unlock=auto_unlock,
                                      score=j, challenge_metadata={},
                                      unlock_requirements=random_rpn_op() if not auto_unlock else "")
                challenge.save()

        print('Creating 20000 users... ', end="", flush=True)
        Member = get_user_model()
        users_to_create = []
        for i in range(10000):
            user = Member(username='user-' + str(i), email='user-' + str(i) + '@example.org')
            user2 = Member(username='user-' + str(i) + '-second',
                                     email='user-' + str(i) + '-second@example.org')
            users_to_create.append(user)
            users_to_create.append(user2)

        timed_log(lambda: Member.objects.bulk_create(users_to_create), "Inserting to database...")

        print('Creating 10000 teams... ', end="", flush=True)
        teams_to_create = []
        members = list(Member.objects.all())
        for i in range(10000):
            team = Team(name='team-' + str(i), password='password', owner=members[i * 2])

            teams_to_create.append(team)

        timed_log(lambda: Team.objects.bulk_create(teams_to_create), "Inserting to database...")

        print("Adding members to teams... ", end="", flush=True)
        members_to_update = []
        teams = list(Team.objects.all())
        for i in range(0, len(members), 2):
            owner = members[i]
            teammate = members[i+1]

            owner.team = teams[i // 2]
            teammate.team = teams[i // 2]

            members_to_update.append(owner)
            members_to_update.append(teammate)

        timed_log(lambda: Member.objects.bulk_update(members_to_update, ["team"]), "Saving to database...")

        print("Creating 1m solves and scores...")
        scores_to_create = []
        solves_to_create = []
        users_to_update = []
        teams_to_update = []
        for team in Team.objects.prefetch_related("members").all():
            z = team.members.all()
            user = z[0]
            user2 = z[1]
            used = []
            for j in range(50):
                points = random.randint(0, 999)
                score = Score(team=team, reason='challenge', points=points, penalty=0, leaderboard=True)
                scores_to_create.append(score)
                solve = Solve(team=team, solved_by=user, challenge_id=(j * 19) + (team.id % 20) + 1, first_blood=False,
                              flag='ractf{}', score=score, correct=True)
                solves_to_create.append(solve)
                user.points += points
                team.points += points
                user.leaderboard_points += points
                team.leaderboard_points += points

                points = random.randint(0, 999)
                score = Score(team=team, reason='challenge', points=points, penalty=0, leaderboard=True)
                scores_to_create.append(score)
                solve = Solve(team=team, solved_by=user2, challenge_id=(j * 19) + (team.id % 20) + 2,
                              first_blood=False, flag='ractf{}', score=score, correct=True)
                solves_to_create.append(solve)
                user2.points += points
                team.points += points
                user.leaderboard_points += points
                team.leaderboard_points += points

            teams_to_update.append(team)
            users_to_update.append(user)
            users_to_update.append(user2)

        timed_log(lambda: Solve.objects.bulk_create(solves_to_create), "[1/4] Saving Solves in database...")
        timed_log(lambda: Member.objects.bulk_update(members_to_update, ["leaderboard_points"]), "[2/4] Saving Members in database...")
        timed_log(lambda: Team.objects.bulk_update(teams_to_update, ["leaderboard_points"]), "[3/4] Saving Teams in database...")
        timed_log(lambda: Score.objects.bulk_create(scores_to_create), "[4/4] Saving Scores in database...")

