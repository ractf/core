from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet


def is_exporting(request):
    return request.user.is_superuser and (request.headers.get('exporting') or request.headers.get('x-exporting'))


class AdminCreateModelViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.is_superuser and not self.request.user.should_deny_admin():
            if self.request.method in permissions.SAFE_METHODS:
                return self.admin_serializer_class
            return self.create_serializer_class
        return self.serializer_class


class AdminModelViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.is_superuser and not self.request.user.should_deny_admin():
            return self.admin_serializer_class
        return self.serializer_class


class AdminListModelViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.request is None:
            return self.admin_serializer_class
        if self.action == 'list' and not is_exporting(self.request):
            if self.request.user.is_superuser and not self.request.user.should_deny_admin():
                return self.list_admin_serializer_class
            return self.list_serializer_class
        if self.request.user.is_superuser and not self.request.user.should_deny_admin():
            return self.admin_serializer_class
        return self.serializer_class
