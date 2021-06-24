"""Tests for core's plugins and plugin system."""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from team.models import Team

from challenge.models import Category, Challenge, Score, Solve
from challenge.tests.mixins import ChallengeSetupMixin
from config import config
from core import plugins
from core.flag.hashed import HashedFlagPlugin
from core.flag.lenient import LenientFlagPlugin
from core.flag.plaintext import PlaintextFlagPlugin
from core.flag.regex import RegexFlagPlugin
from core.points.basic import BasicPointsPlugin
from core.points.decay import DecayPointsPlugin


class HashedFlagPluginTestCase(APITestCase):
    """Tests for HashedFlagPlugin."""

    def setUp(self):
        """Create a challenge and category for testing."""
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
        """A valid flag returns True."""
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_invalid_flag(self):
        """An invalid flag returns False."""
        self.assertFalse(self.plugin.check("ractf{b}"))


class LenientFlagPluginTestCase(APITestCase):
    """Test the LenientFlagPlugin."""

    def setUp(self):
        """Create a category and challenge for testing."""
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
        """A valid flag returns True."""
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_valid_flag_accented(self):
        """Accent characters are correctly replaced."""
        self.assertTrue(self.plugin.check("ractf{à}"))

    def test_valid_flag_invalid_format(self):
        """The flag format is correctly fixed."""
        self.assertTrue(self.plugin.check("a"))

    def test_valid_flag_spaced(self):
        """Whitespace is stripped correctly."""
        self.assertTrue(self.plugin.check("  ractf{a}  "))

    def test_valid_flag_casing(self):
        """The flag validation is case-insensitive."""
        self.assertTrue(self.plugin.check("A"))

    def test_valid_flag_all(self):
        """A flag with all fixable inconsistencies is validated correctly."""
        self.assertTrue(self.plugin.check(" Á"))

    def test_valid_flag_accented_excluded(self):
        """A flag with an accent character is not validated when accent fixing is disabled."""
        self.challenge.flag_metadata["exclude_passes"].append("accent_insensitive")
        self.challenge.save()
        self.assertFalse(self.plugin.check("ractf{à}"))

    def test_valid_flag_invalid_format_excluded(self):
        """A flag in the wrong format is rejected when the flag format is not being fixed."""
        self.challenge.flag_metadata["exclude_passes"].append("format")
        self.challenge.save()
        self.assertFalse(self.plugin.check("a"))

    def test_valid_flag_spaced_excluded(self):
        """A flag with incorrect spacing is rejected when whitespace is not being fixed."""
        self.challenge.flag_metadata["exclude_passes"].append("whitespace_insensitive")
        self.challenge.save()
        self.assertFalse(self.plugin.check("  ractf{a}  "))

    def test_valid_flag_casing_excluded(self):
        """A flag with incorrect casing is rejected when the validator is case sensitive."""
        self.challenge.flag_metadata["exclude_passes"].append("case_insensitive")
        self.challenge.save()
        self.assertFalse(self.plugin.check("A"))

    def test_valid_flag_missing_metadata(self):
        """The flag plugin defaults to fixing everything."""
        self.challenge.flag_metadata.pop("exclude_passes")
        self.assertTrue(self.plugin.check("A"))


class PlaintextFlagPluginTestCase(APITestCase):
    """Tests for PlaintextFlagPlugin."""

    def setUp(self):
        """Create a category and challenge for testing."""
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
        """A valid flag returns True."""
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_invalid_flag(self):
        """An invalid flag returns False."""
        self.assertFalse(self.plugin.check("ractf{b}"))


class RegexFlagPluginTestCase(APITestCase):
    """Tests for RegexFlagPlugin."""

    def setUp(self):
        """Create a category and challenge for testing."""
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
        """A valid flag returns True."""
        self.assertTrue(self.plugin.check("ractf{a}"))

    def test_invalid_flag(self):
        """An invalid flag returns False."""
        self.assertFalse(self.plugin.check("ractf{b}"))

    def test_valid_flag_regex(self):
        """A flag that matches the regex returns True."""
        self.assertTrue(self.plugin.check("abcractf{a}abc"))


class BasicPointsPluginTestCase(APITestCase):
    """Tests for BasicPointsPlugin."""

    def setUp(self):
        """Create a category and challenge for testing."""
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
        """The points value of the challenge is returned."""
        self.assertEqual(self.plugin.get_points(None, None, None), 1000)


class DecayPointsPluginTestCase(ChallengeSetupMixin, APITestCase):
    """Tests for DecayPointsPlugin."""

    def setUp(self):
        """Set the variables for decaying points."""
        super(DecayPointsPluginTestCase, self).setUp()
        self.challenge2.challenge_metadata = {
            "decay_constant": 0.5,
            "min_points": 100,
        }
        self.plugin = DecayPointsPlugin(self.challenge2)

    def test_base_points(self):
        """The base points value is the points value of a challenge."""
        self.assertEqual(self.plugin.get_points(None, None, 0), 1000)

    def test_min_points(self):
        """After a high enough number of solves, the points value eventually reaches the minimum."""
        self.assertEqual(self.plugin.get_points(None, None, 1000000000), 100)

    def test_first_solve_points(self):
        """The first solve should be the base points value."""
        self.assertEqual(self.plugin.get_points(None, None, 1), 1000)

    def test_decaying_points(self):
        """The amount of points should decrease as the solve number gets higher."""
        self.assertTrue(self.plugin.get_points(None, None, 1) > self.plugin.get_points(None, None, 5))

    def test_recalculate(self):
        """User scores are correctly reduced when scores are recalculated."""
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
        self.assertTrue(get_user_model().objects.get(id=self.user.pk).points < points)

    def test_score(self):
        """The score function correctly sets user and team points."""
        config.set("enable_scoring", True)
        self.plugin.score(self.user, self.team, "", Solve.objects.filter(challenge=self.challenge2))
        self.assertEqual(self.team.points, 1000)
        self.assertEqual(self.team.leaderboard_points, 1000)

    def test_score_leaderboard_disabled(self):
        """The score function correctly sets user and team points with the leaderboard disabled."""
        config.set("enable_scoring", False)
        self.plugin.score(self.user, self.team, "", Solve.objects.filter(challenge=self.challenge2))
        self.assertEqual(self.team.points, 1000)
        self.assertEqual(self.team.leaderboard_points, 0)


class PluginLoaderTestCase(APITestCase):
    """Test the plugin loader."""

    def test_plugin_loader_points(self):
        """There are 2 points plugins the plugin loader should find."""
        plugins.load_plugins(["plugins.tests"])
        self.assertEqual(len(plugins.plugins["points"]), 2)

    def test_plugin_loader_flag(self):
        """There are 6 flag plugins the plugin loader should find."""
        plugins.load_plugins(["plugins.tests"])
        self.assertEqual(len(plugins.plugins["flag"]), 6)


class BasePluginTest(ChallengeSetupMixin, APITestCase):
    """Test BasePlugin."""

    def test_dont_track_incorrect_submissions(self):
        """The database should not be interacted with if enable_track_incorrect_submissions is False."""
        config.set("enable_track_incorrect_submissions", False)
        plugin = BasicPointsPlugin(self.challenge2)
        self.assertNumQueries(0, lambda: plugin.register_incorrect_attempt(self.user, self.team, "ractf{}", None))
