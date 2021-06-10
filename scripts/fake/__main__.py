"""A command-line tool for generating and inserting many rows of fake data into the database."""

import random

import psycopg2
from django import db
from faker import Faker

from challenge.models import Category, Challenge, Score, Solve
from member.models import Member
from scripts.fake.config import (
    CATEGORIES,
    CHALLENGES,
    SOLVES,
    TABLE_NAMES,
    TEAMS,
    USERS,
    PostgreSQL,
    arguments,
)
from scripts.fake.utils import TimedLog, random_rpn_op
from team.models import Team


if not arguments.get("--force") and Member.objects.count() > 0:
    print("The database is already populated, clear the db or use --force to run anyway.")
    exit(1)

if arguments.get("clean"):
    with psycopg2.connect(dsn=PostgreSQL.dsn) as connection:
        connection.set_isolation_level(0)
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE {PostgreSQL.DATABASE}")
            cursor.execute(f"CREATE DATABASE {PostgreSQL.DATABASE}")

cursor = db.connection.cursor()

db_constraints = {}
db_indexes = {}

try:
    for table in TABLE_NAMES:
        cursor.execute(
            f"SELECT indexname, indexdef FROM pg_indexes" f"WHERE tablename='{table}' AND indexname != '{table}_pkey';"
        )
        indexes = cursor.fetchall()

        cursor.execute(
            f"SELECT conname, contype, pg_catalog.pg_get_constraintdef(r.oid, true) as condef "
            f"FROM pg_catalog.pg_constraint r WHERE r.conrelid = '{table}'::regclass AND conname != '{table}_pkey';"
        )
        constraints = cursor.fetchall()
        for constraint_name, constraint_type, constraint_sql in constraints:
            cursor.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint_name}")
        for index_name, index_sql in indexes:
            cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
        db.connection.commit()

        db_indexes[table] = indexes
        db_constraints[table] = constraints

    for table in TABLE_NAMES:
        cursor.execute(f"ALTER TABLE {table} SET UNLOGGED")
        db.connection.commit()

    with TimedLog("Inserting data... ", ending="\n"):
        fake = Faker()
        category_ids = []
        with TimedLog(f"Creating {CATEGORIES} categories..."):
            for display_order in range(CATEGORIES):
                category = Category(
                    name=" ".join(fake.words()),
                    display_order=display_order,
                    contained_type="test",
                    description=fake.unique.text(),
                )
                category.save()
                category_ids.append(category.pk)

        challenge_ids = []
        with TimedLog(f"Creating {CHALLENGES} challenges for each category..."):
            for pk in range(CATEGORIES):
                category = Category.objects.get(pk=category_ids[pk])
                for j in range(CHALLENGES):
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
                    challenge_ids.append(challenge.pk)

        with TimedLog(f"Creating {USERS * TEAMS} users in memory..."):
            users_to_create = [
                Member(username=fake.unique.user_name(), email=fake.unique.email()) for _ in range(USERS * TEAMS)
            ]

        with TimedLog("Inserting to database..."):
            Member.objects.bulk_create(users_to_create)

        with TimedLog(f"Creating {TEAMS} teams in memory...."):
            teams_to_create = []
            members = list(Member.objects.all())
            for pk in range(TEAMS):
                team = Team(name=fake.unique.user_name(), password=" ".join(fake.words()), owner=members[pk * USERS])
                teams_to_create.append(team)

        with TimedLog("Inserting to database..."):
            Team.objects.bulk_create(teams_to_create)

        with TimedLog("Adding members to teams in memory..."):
            members_to_update = []
            teams = list(Team.objects.all())
            for index in range(0, len(members)):
                team_member = members[index]
                team_member.team = teams[index // USERS % len(teams)]
                members_to_update.append(team_member)

        with TimedLog("Saving to database..."):
            Member.objects.bulk_update(members_to_update, ["team"])

        with TimedLog(f"Creating {SOLVES} solves and scores in memory..."):
            scores_to_create = []
            solves_to_create = []
            users_to_update = set()
            teams_to_update = set()
            teams = list(Team.objects.prefetch_related("members").all())
            team_index = 0

            for index in range(SOLVES):
                if index != 0 and index % len(challenge_ids) == 0:
                    team_index += 1
                team = teams[team_index]
                user = team.members.all()[index % USERS]

                points = random.randint(0, 999)
                penalty = 0 if random.randint(0, 10) != 5 else random.randint(0, points)
                score = Score(team=team, reason="challenge", points=points, penalty=penalty, leaderboard=True)
                scores_to_create.append(score)
                solve = Solve(
                    team=team,
                    solved_by=user,
                    challenge_id=challenge_ids[index % len(challenge_ids)],
                    first_blood=False,
                    flag="ractf{a}",
                    score=score,
                    correct=True,
                )
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
    for table in TABLE_NAMES:
        for index_name, index_sql in db_indexes[table]:
            cursor.execute(index_sql)
            db.connection.commit()
    for table in TABLE_NAMES:
        for constraint_name, constraint_type, constraint_sql in db_constraints[table]:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} {constraint_sql}")
                db.connection.commit()
            except db.ProgrammingError:  # Some constraints seem to get added implicitly so adding them throws an error
                pass
