from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase


class CatchAllTestCase(APITestCase):
    def test_catchall_404s(self):
        response = self.client.get("/sdgodgsjds")
        self.assertEquals(response.status_code, HTTP_404_NOT_FOUND)
