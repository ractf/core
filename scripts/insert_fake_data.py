import argparse
import os
import random
import sys
import time

import django
from faker import Faker

base_dir = os.path.abspath(
    os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir),
        "src",
    )
)

if base_dir not in sys.path:
    sys.path.insert(1, base_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")
django.setup()

from django.contrib.auth import get_user_model  # noqa
from django.db import ProgrammingError, connection  # noqa

from challenge.models import Category, Challenge, Score, Solve  # noqa
from member.models import Member  # noqa
from team.models import Team  # noqa

parser = argparse.ArgumentParser(description="Insert fake data into the database.")
parser.add_argument("--teams", type=int, help="Number of teams to create", default=10)
parser.add_argument("--users", type=int, help="Number of users to create per team", default=2)
parser.add_argument("--categories", type=int, help="Number of categories to create", default=5)
parser.add_argument("--challenges", type=int, help="Number of challenges to create per category", default=10)
parser.add_argument("--solves", type=int, help="Number of solves to create", default=100)
parser.add_argument("--force", help="Always run, even when the database is populated", action="store_true", default=False)
args = parser.parse_args()


if not args.force and Member.objects.count() > 0:
    print("The database is already populated, clear the db or use --force to run anyway.")
    exit(1)


class TimedLog:
    def __init__(self, msg, ending=" "):
        self.msg = msg
        self.ending = ending

    def __enter__(self):
        self._entry_time = time.time()
        print(self.msg, end=self.ending, flush=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Done (" + str(time.time() - self._entry_time) + "s)")


def random_rpn_op(depth=0):
    depth += 1

    if depth > 4 or (random.randint(1, 4) < 3 and depth > 1):
        return str(random.randint(1, 1000))

    if random.randint(1, 2) == 1:
        return f"{random_rpn_op(depth)} {random_rpn_op(depth)} OR"
    else:
        return f"{random_rpn_op(depth)} {random_rpn_op(depth)} AND"


cursor = connection.cursor()
db_indexes = {}
db_constraints = {}
table_names = [
    "member_member_groups",
    "authentication_token",
    "member_member_user_permissions",
    "authtoken_token",
    "authentication_totpdevice",
    "authentication_backupcode",
    "authentication_passwordresettoken",
    "member_userip",
    "authentication_invitecode",
    "challenge_file",
    "challenge_tag",
    "challenge_challengefeedback",
    "hint_hintuse",
    "hint_hint",
    "challenge_challengevote",
    "challenge_solve",
    "challenge_score",
    "challenge_challenge",
    "challenge_challenge",
    "team_team",
    "member_member",
]
try:
    for table in table_names:
        cursor.execute(f"SELECT indexname, indexdef FROM pg_indexes WHERE tablename='{table}' AND indexname != '{table}_pkey';")
        indexes = cursor.fetchall()

        cursor.execute(
            f"SELECT conname, contype, pg_catalog.pg_get_constraintdef(r.oid, true) as condef FROM pg_catalog.pg_constraint r WHERE r.conrelid = '{table}'::regclass AND conname != '{table}_pkey';"
        )
        constraints = cursor.fetchall()
        for constraint_name, constraint_type, constraint_sql in constraints:
            cursor.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint_name}")
        for index_name, index_sql in indexes:
            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
        connection.commit()

        db_indexes[table] = indexes
        db_constraints[table] = constraints

    for table in table_names:
        cursor.execute(f"ALTER TABLE {table} SET UNLOGGED")
        connection.commit()

    with TimedLog("Inserting data... ", ending="\n"):
        fake = Faker()
        category_ids = []
        with TimedLog(f"Creating {args.categories} categories..."):
            for i in range(args.categories):
                category = Category(name=" ".join(fake.words()), display_order=i, contained_type="test", description=fake.unique.text())
                category.save()
                category_ids.append(category.id)

        challenge_ids = []
        with TimedLog(f"Creating {args.challenges} challenges for each category..."):
            for i in range(args.categories):
                category = Category.objects.get(id=category_ids[i])
                for j in range(args.challenges):
                    auto_unlock = random.randint(1, 5) == 1
                    challenge = Challenge(
                        name=" ".join(fake.words())[:36],
                        category=category,
                        description=fake.unique.text(),
                        flag_metadata={"flag": f"ractf{{{fake.word()}}}"},
                        author=fake.unique.user_name(),
                        score=j,
                        challenge_metadata={},
                        unlock_requirements=random_rpn_op() if not auto_unlock else "",
                    )
                    challenge.save()
                    challenge_ids.append(challenge.id)

        with TimedLog(f"Creating {args.users * args.teams} users in memory..."):
            users_to_create = [Member(username=fake.unique.user_name(), email=fake.unique.email()) for _ in range(args.users * args.teams)]

        with TimedLog("Inserting to database..."):
            Member.objects.bulk_create(users_to_create)

        with TimedLog(f"Creating {args.teams} teams in memory...."):
            teams_to_create = []
            members = list(Member.objects.all())
            for i in range(args.teams):
                team = Team(name=fake.unique.user_name(), password=" ".join(fake.words()), owner=members[i * args.users])

                teams_to_create.append(team)

        with TimedLog("Inserting to database..."):
            Team.objects.bulk_create(teams_to_create)

        with TimedLog("Adding members to teams in memory..."):
            members_to_update = []
            teams = list(Team.objects.all())
            for i in range(0, len(members)):
                team_member = members[i]
                team_member.team = teams[i // args.users % len(teams)]
                members_to_update.append(team_member)

        with TimedLog("Saving to database..."):
            Member.objects.bulk_update(members_to_update, ["team"])

        with TimedLog(f"Creating {args.solves} solves and scores in memory..."):
            scores_to_create = []
            solves_to_create = []
            users_to_update = set()
            teams_to_update = set()
            teams = list(Team.objects.prefetch_related("members").all())
            team_index = 0
            for i in range(args.solves):
                if i != 0 and i % len(challenge_ids) == 0:
                    team_index += 1
                team = teams[team_index]
                user = team.members.all()[i % args.users]

                points = random.randint(0, 999)
                penalty = 0 if random.randint(0, 10) != 5 else random.randint(0, points)
                score = Score(team=team, reason="challenge", points=points, penalty=penalty, leaderboard=True)
                scores_to_create.append(score)
                solve = Solve(team=team, solved_by=user, challenge_id=challenge_ids[i % len(challenge_ids)], first_blood=False, flag="ractf{a}", score=score, correct=True)
                solves_to_create.append(solve)

                user.points += points - penalty
                team.points += points - penalty
                user.leaderboard_points += points - penalty
                team.leaderboard_points += points - penalty

                teams_to_update.add(team)
                users_to_update.add(user)

        with TimedLog("Saving all to database...", ending="\n"):
            with TimedLog("[1/4] Saving Scores in database..."):
                Score.objects.bulk_create(scores_to_create)
            with TimedLog("[2/4] Saving Solves in database..."):
                Solve.objects.bulk_create(solves_to_create)
            with TimedLog("[3/4] Saving Members in database..."):
                Member.objects.bulk_update(users_to_update, ["leaderboard_points"])
            with TimedLog("[4/4] Saving Teams in database..."):
                Team.objects.bulk_update(teams_to_update, ["leaderboard_points"])
finally:
    for table in table_names:
        for index_name, index_sql in db_indexes[table]:
            cursor.execute(index_sql)
            connection.commit()
    for table in table_names:
        for constraint_name, constraint_type, constraint_sql in db_constraints[table]:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} {constraint_sql}")
                connection.commit()
            except ProgrammingError:  # Some constraints seem to get added implicitly so adding them throws an error
                pass
