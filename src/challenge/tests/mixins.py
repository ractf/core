from challenge.models import Category, Challenge
from hint.models import Hint
from member.models import Member
from team.models import Team


class ChallengeSetupMixin:
    """
    Mixin to create dummy challenge objects for use in tests.

    TODO: Deprecate in favour of Model factories and Faker().
    """

    def setUp(self) -> None:
        """Create dummy challenges and any relevant related models."""
        self.category = Category.objects.create(name="test", display_order=0, contained_type="test", description="")
        self.challenge2 = Challenge.objects.create(
            name="test2",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}"},
            author="dave",
            score=1000,
        )
        self.challenge1 = Challenge.objects.create(
            name="test1",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}"},
            author="dave",
            score=1000,
            unlock_requirements=self.challenge2.id,
        )
        self.challenge3 = Challenge.objects.create(
            name="test3",
            category=self.category,
            description="a",
            challenge_type="basic",
            challenge_metadata={},
            flag_type="plaintext",
            flag_metadata={"flag": "ractf{a}"},
            author="dave",
            score=1000,
        )
        self.hint1 = Hint.objects.create(name="hint1", challenge=self.challenge1, text="a", penalty=100)
        self.hint2 = Hint.objects.create(name="hint2", challenge=self.challenge1, text="a", penalty=100)
        self.hint3 = Hint.objects.create(name="hint3", challenge=self.challenge2, text="a", penalty=100)

        self.user = Member.objects.create(username="challenge-test", email="challenge-test@example.org")
        self.team = Team.objects.create(name="team", password="password", owner=self.user)
        self.user.team = self.team
        self.user.save()

        self.user2 = Member.objects.create(username="challenge-test-2", email="challenge-test-2@example.org", team=self.team)
        self.user3 = Member.objects.create(username="challenge-test-3", email="challenge-test-3@example.org")

        self.team2 = Team.objects.create(name="team2", password="password", owner=self.user3)
        self.user3.team = self.team2
        self.user3.save()
