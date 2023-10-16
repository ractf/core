from admin.models import AuditLogEntry
from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet


def is_exporting(request):
    return request.user.is_staff and (request.headers.get("exporting") or request.headers.get("x-exporting"))


class AdminCreateModelViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            if self.request.method in permissions.SAFE_METHODS:
                return self.admin_serializer_class
            return self.create_serializer_class
        return self.serializer_class


class AdminModelViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.request is None:
            return self.admin_serializer_class
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            return self.admin_serializer_class
        return self.serializer_class


class AdminListModelViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.request is None:
            return self.serializer_class
        if self.action == "list" and not is_exporting(self.request):
            if self.request.user.is_staff and not self.request.user.should_deny_admin():
                return self.list_admin_serializer_class
            return self.list_serializer_class
        if self.request.user.is_staff and not self.request.user.should_deny_admin():
            return self.admin_serializer_class
        return self.serializer_class


class AuditLoggedViewSet(ModelViewSet):
    def create(self, request, *args, **kwargs):
        if request.user is not None and request.user.is_staff:
            ret = super().create(request, *args, **kwargs)

            fields = {}
            fields["model_fields"] = ret.data
            fields["model_name"] = self.get_serializer().Meta.model.__name__
            AuditLogEntry.objects.create(user=request.user, username=request.user.username, action="create_model", extra=fields)

            return ret
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if request.user is not None and request.user.is_staff:
            instance = self.get_object()
            fields = {}
            fields["model_fields"] = self.get_serializer(instance).data
            fields["model_name"] = instance._meta.model.__name__
            fields["model_id"] = instance.id
            AuditLogEntry.objects.create(user=request.user, username=request.user.username, action="destroy_model", extra=fields)

            ret = super().destroy(request, *args, **kwargs)

            return ret
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user is not None and request.user.is_staff:
            old_instance = self.get_object() # Keep track of old data
            old_data = self.get_serializer(old_instance).data

            ret = super().update(request, *args, **kwargs)
            
            new_instance = self.get_object() # Get the new data
            new_data = self.get_serializer(new_instance).data

            diffs = {}

            for key, value in new_data.items():
                if old_data.get(key, None) != value:
                    diffs[key] = {
                        "old": old_data.get(key, None),
                        "new": new_data.get(key, None)
                    }
            
            fields = {}
            fields["updated_fields"] = diffs
            fields["model_name"] = new_instance._meta.model.__name__
            fields["model_id"] = new_instance.id
            AuditLogEntry.objects.create(user=request.user, username=request.user.username, action="update_model", extra=fields)

            return ret
        return super().update(request, *args, **kwargs)