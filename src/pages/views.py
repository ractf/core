from rest_framework.viewsets import ModelViewSet

from backend.permissions import AdminOrAnonymousReadOnly
from pages.models import Page
from pages.serializers import PageSerializer


class TagViewSet(ModelViewSet):
    queryset = Page.objects.all()
    permission_classes = (AdminOrAnonymousReadOnly,)
    throttle_scope = "pages"
    serializer_class = PageSerializer
    pagination_class = None
