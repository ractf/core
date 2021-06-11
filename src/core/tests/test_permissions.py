from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.test import APITestCase

from core.permissions import (
    AdminOrAnonymousReadOnly,
    AdminOrReadOnly,
    AdminOrReadOnlyVisible,
    IsBot,
    ReadOnlyBot,
)
from member.models import Member


class PermissionTestMixin:
    def create_request(self, method: str) -> Request:
        request = Request(HttpRequest())
        request.method = method
        return request


class AdminOrReadOnlyVisibleTestCase(PermissionTestMixin, APITestCase):
    def test_admin_safe(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnlyVisible().has_object_permission(request, None, None))

    def test_admin_unsafe(self) -> None:
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnlyVisible().has_object_permission(request, None, None))

    def test_not_admin_safe_visible(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = True
        self.assertTrue(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))

    def test_not_admin_unsafe_visible(self) -> None:
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = True
        self.assertFalse(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))

    def test_not_admin_safe_not_visible(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = False
        self.assertFalse(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))

    def test_not_admin_unsafe_not_visible(self) -> None:
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        obj = type("Object", (object,), {})
        obj.is_visible = False
        self.assertFalse(AdminOrReadOnlyVisible().has_object_permission(request, None, obj))


class AdminOrReadOnlyTestCase(PermissionTestMixin, APITestCase):
    def test_admin_safe(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnly().has_permission(request, None))

    def test_admin_unsafe(self) -> None:
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrReadOnly().has_permission(request, None))

    def test_not_admin_safe(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        self.assertTrue(AdminOrReadOnly().has_permission(request, None))

    def test_not_admin_unsafe(self) -> None:
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com")
        self.assertFalse(AdminOrReadOnly().has_permission(request, None))


class AdminOrAnonymousReadOnlyTestCase(PermissionTestMixin, APITestCase):
    def test_admin_safe(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrAnonymousReadOnly().has_permission(request, None))

    def test_admin_unsafe(self) -> None:
        request = self.create_request("POST")
        request.user = Member(username="permission-test", email="permission-test@gmail.com", is_staff=True)
        self.assertTrue(AdminOrAnonymousReadOnly().has_permission(request, None))

    def test_anonymous_safe(self) -> None:
        request = self.create_request("GET")
        request.user = AnonymousUser()
        self.assertTrue(AdminOrAnonymousReadOnly().has_permission(request, None))

    def test_anonymous_unsafe(self) -> None:
        request = self.create_request("POST")
        request.user = AnonymousUser()
        self.assertFalse(AdminOrAnonymousReadOnly().has_permission(request, None))


class IsBotTestCase(PermissionTestMixin, APITestCase):
    def test_is_bot(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertTrue(IsBot().has_permission(request, None))

    def test_normal_user(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="bot-test", email="bot-test@gmail.com")
        self.assertFalse(IsBot().has_permission(request, None))


class ReadOnlyBotTestCase(PermissionTestMixin, APITestCase):
    def test_is_bot_safe_method(self) -> None:
        request = self.create_request("GET")
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertTrue(ReadOnlyBot().has_permission(request, None))

    def test_is_bot_unsafe_method(self) -> None:
        request = self.create_request("POST")
        request.user = Member(username="bot-test", email="bot-test@gmail.com", is_bot=True)
        self.assertFalse(ReadOnlyBot().has_permission(request, None))
