from rest_framework.viewsets import ModelViewSet

from pages.models import Page
from pages.serializers import PageSerializer
from backend.permissions import AdminOrReadOnly


class TagViewSet(ModelViewSet):
    queryset = Page.objects.all()
    permission_classes = (AdminOrReadOnly,)
    throttle_scope = 'pages'
    serializer_class = PageSerializer
    pagination_class = None
