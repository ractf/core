import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from backend.exceptions import FormattedException


def handle_request(method, path, **kwargs):
    response = requests.request(method, f"{settings.POLARIS_URL}/{path}", auth=HTTPBasicAuth(settings.POLARIS_USERNAME, settings.POLARIS_PASSWORD), **kwargs)
    if 200 <= response.status_code < 300:
        return response.json()
    elif response.status_code == HTTP_401_UNAUTHORIZED:
        raise FormattedException(status_code=HTTP_401_UNAUTHORIZED, m="polaris_unauthorized")
    elif response.status_code == HTTP_403_FORBIDDEN:
        raise FormattedException(status_code=HTTP_403_FORBIDDEN, m="polaris_permission_denied")
    else:
        raise FormattedException(m="polaris_error", d=response.json())


def get(path, **kwargs):
    return handle_request("GET", path, **kwargs)


def post(path, **kwargs):
    return handle_request("POST", path, **kwargs)


def put(path, **kwargs):
    return handle_request("PUT", path, **kwargs)


def delete(path, **kwargs):
    return handle_request("DELETE", path, **kwargs)


def list_challenges(filter=""):
    return get(f"/challenges?filter={filter}")


def get_challenge(challenge):
    return get(f"/challenges/{challenge}")


def submit_challenge(challenge):
    return post("/challenges", json=challenge)


def delete_challenge(challenge):
    return post(f"/challenges/{challenge}")


def list_deployments(deployment_filter="", challenge_filter=""):
    return get(f"/deployments?filter={deployment_filter}&challengefilter={challenge_filter}")


def get_deployment(deployment):
    return get(f"/deployments/{deployment}")


def submit_deployment(deployment):
    return post("/deployments", json=deployment)


def delete_deployment(deployment):
    return post(f"/deployments/{deployment}")


def list_hosts(filter=""):
    return get(f"/hosts?filter={filter}")


def get_host(id):
    return get(f"/hosts/{id}")


def censor_instance(instance):
    del instance["randomEnv"]
    ports = []
    for port in instance["ports"]:
        if port["advertised"]:
            ports.append(port)
    instance["ports"] = ports
    return instance


def allocate_instance(challenge_id, user):
    response = post("/instanceallocation", json={"challenge": str(challenge_id), "user": str(user.id), "team": str(user.team.id)})
    if not user.is_superuser:
        return censor_instance(response)
    return response


def reallocate_instance(challenge_id, user):
    response = post("/instanceallocation/new", json={"challenge": str(challenge_id), "user": str(user.id), "team": str(user.team.id)})
    if not user.is_superuser:
        return censor_instance(response)
    return response


def list_instances(host_filter="", challenge_filter=""):
    return get(f"/instances?hostfilter={host_filter}&challengefilter={challenge_filter}")
