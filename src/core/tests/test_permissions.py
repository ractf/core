"""Tests for permissions defined by the core app."""

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.test import APITestCase

from core.permissions import (
    AdminOrAnonymousReadOnly,
    AdminOrReadOnly,
    AdminOrReadOnlyVisible,
    IsBot,
    IsSudo,
    ReadOnlyBot,
)
from teams.models import Member


class PermissionTestMixin:
    """Mixin to add common functionality to permissions tests."""

    def create_request(self, method: str) -> Request:
        """Return a request with the specified method."""
        request = Request(HttpRequest())
        request.method = method
        return request


class AdminOrReadOnlyVisibleTestCase(PermissionTestMixin, APITestCase):
    """Tests for the AdminOrReadOnlyVisible permission."""

    def test_admin_safe(self) -> None:
        """An admin should be able to use a safe method."""
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnlyVisible().has_object_permission(request, None, None))

    def test_admin_unsafe(self) -> None:
        """An admin should be able to use an unsafe method."""
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnlyVisible().has_object_permission(request, None, None))

    def test_not_admin_safe_visible(self) -> None:
        """A non admin should be able to use a safe method."""
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = True
        self.assertTrue(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))

    def test_not_admin_unsafe_visible(self) -> None:
        """A non admin should not be able to use an unsafe method."""
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = True
        self.assertFalse(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))

    def test_not_admin_safe_not_visible(self) -> None:
        """A non admin should not be able to use a safe method on a non visible object."""
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = False
        self.assertFalse(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))

    def test_not_admin_unsafe_not_visible(self) -> None:
        """A non admin should not be able to use an unsafe method."""
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = False
        self.assertFalse(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))


class AdminOrReadOnlyTestCase(PermissionTestMixin, APITestCase):
    """Tests for the AdminOrReadOnly permission."""

    def test_admin_safe(self) -> None:
        """An admin should be able to access a view using a safe method."""
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnly().has_permission(request, None))

    def test_admin_unsafe(self) -> None:
        """An admin should be able to access a view using an unsafe method."""
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnly().has_permission(request, None))

    def test_not_admin_safe(self) -> None:
        """An non-admin should be able to access a view using a safe method."""
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        self.assertTrue(AdminOrReadOnly().has_permission(request, None))

    def test_not_admin_unsafe(self) -> None:
        """An non-admin should not be able to access a view using an unsafe method."""
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        self.assertFalse(AdminOrReadOnly().has_permission(request, None))


class AdminOrAnonymousReadOnlyTestCase(PermissionTestMixin, APITestCase):
    """Tests for the AdminOrAnonymousReadOnly permission."""

    def test_admin_safe(self) -> None:
        """An admin should be able to access a view using a safe method."""
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrAnonymousReadOnly().has_permission(request, None))

    def test_admin_unsafe(self) -> None:
        """An admin should be able to access a view using an unsafe method."""
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrAnonymousReadOnly().has_permission(request, None))

    def test_anonymous_safe(self) -> None:
        """An anonymous user should be able to access a view using a safe method."""
        request = self.create_request("GET")
        request.user = AnonymousUser()
        self.assertTrue(AdminOrAnonymousReadOnly().has_permission(request, None))

    def test_anonymous_unsafe(self) -> None:
        """An anonymous user should not be able to access a view using an unsafe method."""
        request = self.create_request("POST")
        request.user = AnonymousUser()
        self.assertFalse(AdminOrAnonymousReadOnly().has_permission(request, None))


class IsBotTestCase(PermissionTestMixin, APITestCase):
    """Tests for the IsBot permission."""

    def test_is_bot(self) -> None:
        """A bot should be able to access this view."""
        request = self.create_request("GET")
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertTrue(IsBot().has_permission(request, None))

    def test_normal_user(self) -> None:
        """A normal user should not be able to access this view."""
        request = self.create_request("GET")
        request.user = Member(username="bot-test", email="bot-test@gmail.com")
        self.assertFalse(IsBot().has_permission(request, None))


class ReadOnlyBotTestCase(PermissionTestMixin, APITestCase):
    """Tests for the ReadOnlyBot permission."""

    def test_is_bot_safe_method(self) -> None:
        """A bot should be able to access this view with a safe method."""
        request = self.create_request("GET")
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertTrue(ReadOnlyBot().has_permission(request, None))

    def test_is_bot_unsafe_method(self) -> None:
        """A bot should not be able to access this view with an unsafe method."""
        request = self.create_request("POST")
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertFalse(ReadOnlyBot().has_permission(request, None))


class IsSudoTestCase(PermissionTestMixin, APITestCase):
    """Tests for the IsSudo permission."""

    def test_is_sudo(self) -> None:
        """A sudo user should be able to access this view."""
        request = self.create_request("GET")
        request.sudo = True
        self.assertTrue(IsSudo().has_permission(request, None))

    def test_is_not_sudo(self) -> None:
        """A non-sudo user should not be able to access this view."""
        request = self.create_request("POST")
        self.assertFalse(IsSudo().has_permission(request, None))
