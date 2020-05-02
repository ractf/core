import re
from json import loads

import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_200_OK
from rest_framework.views import APIView

from backend import settings
from backend.response import FormattedResponse

replace_objects_regex = re.compile(r"<.+:.+>")


def get_current_instance(user_id):
    response = requests.get(f"{settings.CHALLENGE_SERVER_URL}/user/{user_id}",
                            headers={"Authorization": settings.CHALLENGE_SERVER_API_KEY})
    if response.status_code == HTTP_404_NOT_FOUND:
        return None
    return get_json_from_response(response)


def disconnect_user(user_id):
    response = requests.post(f"{settings.CHALLENGE_SERVER_URL}/disconnect/{user_id}",
                             headers={"Authorization": settings.CHALLENGE_SERVER_API_KEY})
    if response.status_code == HTTP_200_OK:
        return True
    return False


def get_new_instance(challenge_id, user_id):
    response = requests.post(settings.CHALLENGE_SERVER_URL, json={
        "user": user_id,
        "challenge": challenge_id
    }, headers={"Authorization": settings.CHALLENGE_SERVER_API_KEY})
    if response.status_code == HTTP_200_OK:
        return get_json_from_response(response)
    return False


def return_instance_or_create_new(challenge_id, user_id):
    current_instance = get_current_instance(user_id)
    if current_instance is None:
        return format_json(get_new_instance(challenge_id, user_id))
    elif current_instance["challenge"] == challenge_id:
        return format_json(current_instance)
    else:
        disconnect_user(user_id)
        return format_json(get_new_instance(challenge_id, user_id))


def request_reset(user_id, challenge_id):
    current_instance = get_current_instance(user_id)
    if current_instance is None:
        return return_instance_or_create_new(challenge_id, user_id)
    elif current_instance["challenge"] != challenge_id:
        return return_instance_or_create_new(challenge_id, user_id)

    response = requests.post(f"{settings.CHALLENGE_SERVER_URL}/reset/{current_instance['container_id']}",
                             headers={"Authorization": settings.CHALLENGE_SERVER_API_KEY},
                             json={"user": str(user_id)})

    if response.status_code in [HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN]:
        return return_instance_or_create_new(challenge_id, user_id)
    return format_json(get_json_from_response(response))


def get_json_from_response(response):
    return loads(re.sub(replace_objects_regex, '"[Object]"', response.text.replace("'", '"'))[1:-1])


def format_json(json):
    if type(json) == str:
        json_data = loads(json)
    else:
        json_data = json
    return {"ip": settings.CHALLENGE_SERVER_IP, "port": json_data["port"]}


class RequestInstanceOrGetCurrentInstance(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'challenge_instance_get'

    def get(self, request, challenge_id):
        return FormattedResponse(return_instance_or_create_new(challenge_id, request.user.id))


class RequestReset(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'challenge_instance_reset'

    def get(self, request, challenge_id):
        return FormattedResponse(request_reset(request.user.id, challenge_id))


class DisconnectFromAllInstances(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        disconnect_user(request.user.id)
        return FormattedResponse()
