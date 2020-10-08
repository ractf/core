from rest_framework.viewsets import ModelViewSet

from pages.models import Page
from pages.serializers import PageSerializer
from backend.permissions import AdminOrAnonymousReadOnly


class TagViewSet(ModelViewSet):
    """
    list:
    Retrieve all pages.

    create:
    Create a new page.

    retrieve:
    Retrieve a page.

    update:
    Update a page.

    partial_update:
    Partially update a page.

    destroy:
    Delete a page.
    """
    
    queryset = Page.objects.all()
    permission_classes = (AdminOrAnonymousReadOnly,)
    throttle_scope = 'pages'
    serializer_class = PageSerializer
    pagination_class = None
