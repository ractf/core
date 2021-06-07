from django.core.cache import caches
from django.db import connection

import config


def get_solve_counts():
    cache = caches["default"]
    solve_counts = cache.get("solve_counts")
    if solve_counts is not None and config.config.get("enable_caching"):
        return solve_counts
    with connection.cursor() as cursor:
        cursor.execute("SELECT challenge_id, COUNT(*) FROM challenge_solve WHERE correct=true GROUP BY challenge_id;")
        solve_counts = {i[0]: i[1] for i in cursor.fetchall()}
    cache.set("solve_counts", solve_counts, 15)
    return solve_counts


def get_incorrect_solve_counts():
    cache = caches["default"]
    solve_counts = cache.get("incorrect_solve_counts")
    if solve_counts is not None and config.config.get("enable_caching"):
        return solve_counts
    with connection.cursor() as cursor:
        cursor.execute("SELECT challenge_id, COUNT(*) FROM challenge_solve WHERE correct=false GROUP BY challenge_id;")
        solve_counts = {i[0]: i[1] for i in cursor.fetchall()}
    cache.set("incorrect_solve_counts", solve_counts, 15)
    return solve_counts


def get_positive_votes():
    cache = caches["default"]
    positive_votes = cache.get("positive_votes")
    if positive_votes is not None and config.config.get("enable_caching"):
        return positive_votes
    with connection.cursor() as cursor:
        cursor.execute("SELECT challenge_id, COUNT(*) FROM challenge_challengevote WHERE positive=true GROUP BY challenge_id;")
        positive_votes = {i[0]: i[1] for i in cursor.fetchall()}
    cache.set("positive_votes", cache.get("positive_votes"), 15)
    return positive_votes


def get_negative_votes():
    cache = caches["default"]
    negative_votes = cache.get("negative_votes")
    if negative_votes is not None and config.config.get("enable_caching"):
        return negative_votes
    with connection.cursor() as cursor:
        cursor.execute("SELECT challenge_id, COUNT(*) FROM challenge_challengevote WHERE positive=false GROUP BY challenge_id;")
        negative_votes = {i[0]: i[1] for i in cursor.fetchall()}
    cache.set("negative_votes", cache.get("negative_votes"), 15)
    return negative_votes
