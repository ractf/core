from typing import Type

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet


def is_exporting(request: Request):
    return request.user.is_staff and (request.headers.get('exporting') or request.headers.get('x-exporting'))


class AdminCreateModelViewSet(ModelViewSet):
    admin_serializer_class: Type[Serializer] = None
    create_serializer_class: Type[Serializer] = None

    def get_serializer_class(self) -> Type[Serializer]:
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.has_admin_permissions():
            if self.request.method in permissions.SAFE_METHODS:
                return self.admin_serializer_class
            return self.create_serializer_class
        return self.serializer_class


class AdminModelViewSet(ModelViewSet):
    admin_serializer_class: Type[Serializer] = None

    def get_serializer_class(self) -> Type[Serializer]:
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.has_admin_permissions():
            return self.admin_serializer_class
        return self.serializer_class


class AdminListModelViewSet(ModelViewSet):
    admin_serializer_class: Type[Serializer] = None
    create_serializer_class: Type[Serializer] = None
    list_serializer_class: Type[Serializer] = None
    list_admin_serializer_class: Type[Serializer] = None

    def get_serializer_class(self) -> Type[Serializer]:
        if self.request is None:
            return self.admin_serializer_class
        if self.action == 'list' and not is_exporting(self.request):
            if self.request.user.has_admin_permissions():
                return self.list_admin_serializer_class
            return self.list_serializer_class
        if self.request.user.has_admin_permissions():
            return self.admin_serializer_class
        return self.serializer_class
