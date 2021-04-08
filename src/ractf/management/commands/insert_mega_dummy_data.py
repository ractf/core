import random
import time

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.db import transaction

from challenge.models import Challenge, Category, Score, Solve
from team.models import Team


class TimedLog:
    def __init__(self, msg, ending=" "):
        self.msg = msg
        self.ending = ending

    def __enter__(self):
        self._entry_time = time.time()
        print(self.msg, end=self.ending, flush=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Done (" + str(time.time() - self._entry_time) + "s)")


class Command(BaseCommand):

    def handle(self, *args, **options):
        with TimedLog("Inserting phat dummy data... ", ending="\n"):
            with TimedLog("Creating 10 categories..."):
                for i in range(10):
                    category = Category(name='category-' + str(i), display_order=i, contained_type='test',
                                        description='Category ' + str(i))
                    category.save()

            def random_rpn_op(depth=0):
                depth += 1

                if depth > 4 or (random.randint(1, 4) < 3 and depth > 1):
                    return str(random.randint(1, 1000))

                if random.randint(1, 2) == 1:
                    return f"{random_rpn_op(depth)} {random_rpn_op(depth)} OR"
                else:
                    return f"{random_rpn_op(depth)} {random_rpn_op(depth)} AND"

            with TimedLog('Creating 100 challenges for each category...'):
                for i in range(10):
                    category = Category.objects.get(name='category-' + str(i))
                    for j in range(100):
                        auto_unlock = (random.randint(1, 5) == 1)
                        challenge = Challenge(name='cat-' + str(i) + '-chal-' + str(j), category=category,
                                              description='An example challenge ' + str(j),
                                              flag_metadata={'flag': f'ractf{{{j}}}'}, author='dave',
                                              score=j, challenge_metadata={},
                                              unlock_requirements=random_rpn_op() if not auto_unlock else "")
                        challenge.save()

            with TimedLog("Creating 20k users in memory..."):
                Member = get_user_model()
                users_to_create = []
                for i in range(10000):
                    user = Member(username='user-' + str(i), email='user-' + str(i) + '@example.org')
                    user2 = Member(username='user-' + str(i) + '-second',
                                             email='user-' + str(i) + '-second@example.org')
                    users_to_create.append(user)
                    users_to_create.append(user2)

            with TimedLog("Inserting to database..."):
                Member.objects.bulk_create(users_to_create)

            with TimedLog("Creating 10k teams in memory...."):
                teams_to_create = []
                members = list(Member.objects.all())
                for i in range(10000):
                    team = Team(name='team-' + str(i), password='password', owner=members[i * 2])

                    teams_to_create.append(team)

            with TimedLog("Inserting to database..."):
                Team.objects.bulk_create(teams_to_create)

            with TimedLog("Adding members to teams in memory..."):
                members_to_update = []
                teams = list(Team.objects.all())
                for i in range(0, len(members), 2):
                    owner = members[i]
                    teammate = members[i+1]

                    owner.team = teams[i // 2]
                    teammate.team = teams[i // 2]

                    members_to_update.append(owner)
                    members_to_update.append(teammate)

            with TimedLog("Saving to database..."):
                Member.objects.bulk_update(members_to_update, ["team"])

            with TimedLog("Creating 1m solves and scores in memory..."):
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

            with TimedLog("Saving all to database...", ending="\n"):
                with TimedLog("[1/4] Saving Solves in database..."):
                    Solve.objects.bulk_create(solves_to_create)
                with TimedLog("[2/4] Saving Members in database..."):
                    Member.objects.bulk_update(members_to_update, ["leaderboard_points"])
                with TimedLog("[3/4] Saving Teams in database..."):
                    Team.objects.bulk_update(teams_to_update, ["leaderboard_points"])
                with TimedLog("[4/4] Saving Scores in database..."):
                    Score.objects.bulk_create(scores_to_create)

