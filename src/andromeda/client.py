from uuid import UUID

import requests
from django.conf import settings
from rest_framework.status import HTTP_200_OK

from backend.exceptions import FormattedException


def post(path, **kwargs):
    response = requests.post(
        f"{settings.ANDROMEDA_URL}/{path}",
        headers={"Authorization": settings.ANDROMEDA_API_KEY},
        timeout=settings.ANDROMEDA_TIMEOUT,
        **kwargs,
    )
    if response.status_code == HTTP_200_OK:
        return response.json()
    raise FormattedException(m="challenge_server_error")


def get(path, **kwargs):
    response = requests.get(
        f"{settings.ANDROMEDA_URL}/{path}",
        headers={"Authorization": settings.ANDROMEDA_API_KEY},
        timeout=settings.ANDROMEDA_TIMEOUT,
        **kwargs,
    )
    if response.status_code == HTTP_200_OK:
        return response.json()
    raise FormattedException(m="challenge_server_error")


def get_instance(user_id, job_id):
    return post("", json={"user": str(user_id), "job": job_id})


def request_reset(user_id, job_id):
    return post("reset", json={"user": str(user_id), "job": job_id})


def list_jobs():
    return get("jobs")


def restart_job(job_id):
    try:
        UUID(job_id)
    except ValueError:
        return {}
    return post(f"job/{job_id}/restart")


def list_instances():
    return get("instances")


def sysinfo():
    return get("sysinfo")


def submit_job(job_spec):
    return post("job/submit", json=job_spec)
