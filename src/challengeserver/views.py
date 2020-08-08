from json import loads

import requests
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from backend.exceptions import FormattedException
from backend.response import FormattedResponse


def get_instance(challenge_id, user_id):
    response = requests.post(settings.CHALLENGE_SERVER_URL, json={
        "user": str(user_id),
        "job": challenge_id
    }, headers={"Authorization": settings.CHALLENGE_SERVER_API_KEY})
    if response.status_code == HTTP_200_OK:
        return format_json(response.json())
    raise FormattedException(m='challenge_server_error')


def request_reset(user_id, challenge_id):
    response = requests.post(f"{settings.CHALLENGE_SERVER_URL}/reset", json={
        "user": str(user_id),
        "job": challenge_id
    }, headers={"Authorization": settings.CHALLENGE_SERVER_API_KEY})

    if response.status_code == HTTP_200_OK:
        return format_json(response.json())
    raise FormattedException(m='challenge_server_error')


def format_json(json):
    if type(json) == str:
        json_data = loads(json)
    else:
        json_data = json
    return {"ip": settings.CHALLENGE_SERVER_IP, "port": json_data["port"]}


class RequestInstanceOrGetCurrentInstance(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_get"

    def get(self, request, challenge_id):
        return FormattedResponse(
            get_instance(challenge_id, request.user.id)
        )


class RequestReset(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_reset"

    def get(self, request, challenge_id):
        return FormattedResponse(
            request_reset(request.user.id, challenge_id)
        )
