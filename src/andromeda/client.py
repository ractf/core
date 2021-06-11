"""A simple andromeda API client."""

from uuid import UUID

import requests
from django.conf import settings
from rest_framework.status import HTTP_200_OK

from core.exceptions import FormattedException


def post(path, **kwargs):
    """Send a post request to andromeda."""
    response = requests.post(
        f"{settings.ANDROMEDA_URL}/{path}", headers={"Authorization": settings.ANDROMEDA_API_KEY}, **kwargs
    )
    if response.status_code == HTTP_200_OK:
        return response.json()
    raise FormattedException(m="challenge_server_error")


def get(path, **kwargs):
    """Send a get request to andromeda."""
    response = requests.get(
        f"{settings.ANDROMEDA_URL}/{path}", headers={"Authorization": settings.ANDROMEDA_API_KEY}, **kwargs
    )
    if response.status_code == HTTP_200_OK:
        return response.json()
    raise FormattedException(m="challenge_server_error")


def get_instance(user_id, job_id):
    """Get a challenge instance of a given job id for a user."""
    return post("", json={"user": str(user_id), "job": job_id})


def request_reset(user_id, job_id):
    """Reset a challenge instance of a given job id for a user."""
    return post("reset", json={"user": str(user_id), "job": job_id})


def list_jobs():
    """Get a list of all jobs running on the andromeda host."""
    return get("jobs")


def restart_job(job_id):
    """Restarts a job with a given uuid"""
    try:
        UUID(job_id)
    except ValueError:
        return {}
    return post(f"job/{job_id}/restart")


def list_instances():
    """List all the instances of challenges on the andromeda host."""
    return get("instances")


def sysinfo():
    """Gets the current system info of the andromeda host."""
    return get("sysinfo")


def submit_job(job_spec):
    """Submit a job to the andromeda host."""
    return post("job/submit", json=job_spec)
