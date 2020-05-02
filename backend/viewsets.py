from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet


class AdminCreateModelViewSet(ModelViewSet):

    def get_serializer_class(self):
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            if self.request.method in permissions.SAFE_METHODS:
                return self.admin_serializer_class
            else:
                return self.create_serializer_class
        return self.serializer_class


class AdminModelViewSet(ModelViewSet):

    def get_serializer_class(self):
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            return self.admin_serializer_class
        return self.serializer_class


class AdminListModelViewSet(ModelViewSet):

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.user.is_staff and not self.request.user.should_deny_admin():
                return self.list_admin_serializer_class
            return self.list_serializer_class
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            return self.admin_serializer_class
        return self.serializer_class
