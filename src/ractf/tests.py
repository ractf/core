from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from member.models import UserIP, Member


class GroupIpsTest(TestCase):
    def setUp(self):
        one = Member(username="one", email="one@one.one")
        one.save()

        two = Member(username="two", email="two@two.two")
        two.save()

        three = Member(username="three", email="three@three.three")
        three.save()

        UserIP.objects.create(user=one, ip="1.1.1.1", user_agent="Django Tests")
        UserIP.objects.create(user=two, ip="1.1.1.1", user_agent="Django Tests")
        UserIP.objects.create(user=three, ip="2.2.2.2", user_agent="Django Tests")

    def test_group_ips(self):
        out = StringIO()
        call_command("group_ips", stdout=out)
        self.assertIn("1.1.1.1", out.getvalue())

    def test_group_ips_multiple(self):
        out = StringIO()
        call_command("group_ips", "--multiple", stdout=out)
        self.assertIn("1.1.1.1", out.getvalue())
        self.assertNotIn("2.2.2.2", out.getvalue())

    def test_group_ips_json(self):
        out = StringIO()
        call_command("group_ips", "--json", stdout=out)
        self.assertIn("1.1.1.1", out.getvalue())

    def test_group_ips_multiple_json(self):
        out = StringIO()
        call_command("group_ips", "--json", "--multiple", stdout=out)
        self.assertIn("1.1.1.1", out.getvalue())
        self.assertNotIn("2.2.2.2", out.getvalue())
