from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from challenge.models import Category, Challenge, Score, Solve
from challenge.tests.mixins import ChallengeSetupMixin
from config import config
from plugins import plugins
from plugins.flag.hashed import HashedFlagPlugin
from plugins.flag.lenient import LenientFlagPlugin
from plugins.flag.plaintext import PlaintextFlagPlugin
from plugins.flag.regex import RegexFlagPlugin
from plugins.points.basic import BasicPointsPlugin
from plugins.points.decay import DecayPointsPlugin
from team.models import Team


class HashedFlagPluginTestCase(APITestCase):
    def setUp(self):
        category = Category(name="test", display_order=0, contained_type="test", description="")
        category.save()
        challenge = Challenge(
            name="test1",
            category=category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "9340563721a110d2c9175507f8947f111568cf21ef2aff545e3f93238f63ff32"},
            author="dave",
            score=1000,
        )
        challenge.save()
        self.challenge = challenge
        self.plugin = HashedFlagPlugin(self.challenge)

    def test_valid_flag(self):
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_invalid_flag(self):
        self.assertFalse(self.plugin.check("ractf{b}"))


class LenientFlagPluginTestCase(APITestCase):
    def setUp(self):
        category = Category(name="test", display_order=0, contained_type="test", description="")
        category.save()
        challenge = Challenge(
            name="test1",
            category=category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}", "exclude_passes": []},
            author="dave",
            score=1000,
        )
        challenge.save()
        self.challenge = challenge
        self.plugin = LenientFlagPlugin(self.challenge)

    def test_valid_flag(self):
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_valid_flag_accented(self):
        self.assertTrue(self.plugin.check("ractf{à}"))

    def test_valid_flag_invalid_format(self):
        self.assertTrue(self.plugin.check("a"))

    def test_valid_flag_spaced(self):
        self.assertTrue(self.plugin.check("  ractf{a}  "))

    def test_valid_flag_casing(self):
        self.assertTrue(self.plugin.check("A"))

    def test_valid_flag_all(self):
        self.assertTrue(self.plugin.check(" Á"))

    def test_valid_flag_accented_excluded(self):
        self.challenge.flag_metadata["exclude_passes"].append("accent_insensitive")
        self.challenge.save()
        self.assertFalse(self.plugin.check("ractf{à}"))

    def test_valid_flag_invalid_format_excluded(self):
        self.challenge.flag_metadata["exclude_passes"].append("format")
        self.challenge.save()
        self.assertFalse(self.plugin.check("a"))

    def test_valid_flag_spaced_excluded(self):
        self.challenge.flag_metadata["exclude_passes"].append("whitespace_insensitive")
        self.challenge.save()
        self.assertFalse(self.plugin.check("  ractf{a}  "))

    def test_valid_flag_casing_excluded(self):
        self.challenge.flag_metadata["exclude_passes"].append("case_insensitive")
        self.challenge.save()
        self.assertFalse(self.plugin.check("A"))

    def test_valid_flag_missing_metadata(self):
        self.challenge.flag_metadata.pop("exclude_passes")
        self.assertTrue(self.plugin.check("A"))


class PlaintextFlagPluginTestCase(APITestCase):
    def setUp(self):
        category = Category(name="test", display_order=0, contained_type="test", description="")
        category.save()
        challenge = Challenge(
            name="test1",
            category=category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}"},
            author="dave",
            score=1000,
        )
        challenge.save()
        self.challenge = challenge
        self.plugin = PlaintextFlagPlugin(self.challenge)

    def test_valid_flag(self):
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_invalid_flag(self):
        self.assertFalse(self.plugin.check("ractf{b}"))


class RegexFlagPluginTestCase(APITestCase):
    def setUp(self):
        category = Category(name="test", display_order=0, contained_type="test", description="")
        category.save()
        challenge = Challenge(
            name="test1",
            category=category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": ".*ractf{a}.*"},
            author="dave",
            score=1000,
        )
        challenge.save()
        self.challenge = challenge
        self.plugin = RegexFlagPlugin(self.challenge)

    def test_valid_flag(self):
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_invalid_flag(self):
        self.assertFalse(self.plugin.check("ractf{b}"))

    def test_valid_flag_regex(self):
        self.assertTrue(self.plugin.check("abcractf{a}abc"))


class BasicPointsPluginTestCase(APITestCase):
    def setUp(self):
        category = Category(name="test", display_order=0, contained_type="test", description="")
        category.save()
        challenge = Challenge(
            name="test1",
            category=category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}"},
            author="dave",
            score=1000,
        )
        challenge.save()
        self.challenge = challenge
        self.plugin = BasicPointsPlugin(challenge)

    def test_points(self):
        self.assertEqual(self.plugin.get_points(None, None, None), 1000)


class DecayPointsPluginTestCase(ChallengeSetupMixin, APITestCase):
    def setUp(self):
        super(DecayPointsPluginTestCase, self).setUp()
        self.challenge2.challenge_metadata = {
            "decay_constant": 0.5,
            "min_points": 100,
        }
        self.plugin = DecayPointsPlugin(self.challenge2)

    def test_base_points(self):
        self.assertEqual(self.plugin.get_points(None, None, 0), 1000)

    def test_min_points(self):
        self.assertEqual(self.plugin.get_points(None, None, 1000000000), 100)

    def test_first_solve_points(self):
        self.assertEqual(self.plugin.get_points(None, None, 1), 1000)

    def test_decaying_points(self):
        self.assertTrue(self.plugin.get_points(None, None, 1) > self.plugin.get_points(None, None, 5))

    def test_recalculate(self):
        points = self.plugin.get_points(None, None, 0)
        score = Score(team=self.team, reason="test", points=points)
        score.save()
        solve = Solve(team=self.team, solved_by=self.user, challenge=self.challenge2, score=score, flag="")
        solve.save()
        self.team.points += points
        self.team.leaderboard_points += points
        self.user.points += points
        self.user.leaderboard_points += points
        self.team.save()
        self.user.save()
        score = Score(team=self.team2, reason="test", points=points)
        score.save()
        solve = Solve(team=self.team2, solved_by=self.user3, challenge=self.challenge2, score=score, flag="")
        solve.save()
        self.team2.points += points
        self.team2.leaderboard_points += points
        self.user3.points += points
        self.user3.leaderboard_points += points
        self.team2.save()
        self.user3.save()
        self.plugin.recalculate(
            teams=Team.objects.filter(solves__challenge=self.challenge2),
            users=get_user_model().objects.filter(solves__challenge=self.challenge2),
            solves=Solve.objects.filter(challenge=self.challenge2),
        )
        self.assertTrue(get_user_model().objects.get(id=self.user.id).points < points)

    def test_score(self):
        config.set("enable_scoring", True)
        self.plugin.score(self.user, self.team, "", Solve.objects.filter(challenge=self.challenge2))
        self.assertEqual(self.team.points, 1000)
        self.assertEqual(self.team.leaderboard_points, 1000)

    def test_score_lb_disabled(self):
        config.set("enable_scoring", False)
        self.plugin.score(self.user, self.team, "", Solve.objects.filter(challenge=self.challenge2))
        self.assertEqual(self.team.points, 1000)
        self.assertEqual(self.team.leaderboard_points, 0)


class PluginLoaderTestCase(APITestCase):
    def test_plugin_loader(self):
        plugins.load_plugins(["plugins.tests"])
        # TODO: why is this loading 5
        # self.assertEqual(len(plugins.plugins['flag']), 4)
        self.assertEqual(len(plugins.plugins["points"]), 2)


class BasePluginTest(ChallengeSetupMixin, APITestCase):
    def test_dont_track_incorrect_submissions(self):
        config.set("enable_track_incorrect_submissions", False)
        plugin = BasicPointsPlugin(self.challenge2)
        self.assertNumQueries(0, lambda: plugin.register_incorrect_attempt(self.user, self.team, "ractf{}", None))
