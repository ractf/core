"""API endpoints for the andromeda integration."""

from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from andromeda import client
from andromeda.serializers import JobSubmitRawSerializer, JobSubmitSerializer
from challenge.models import Challenge
from core.response import FormattedResponse


class GetInstanceView(APIView):
    """Endpoint for getting an instance of a given challenge."""

    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_get"

    def get(self, request, job_id):
        """Given a job id, return an instance of the relevant challenge for this user."""
        return FormattedResponse(client.get_instance(request.user.pk, job_id))


class ResetInstanceView(APIView):
    """Endpoint for resetting an instance of a given challenge."""

    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_reset"

    def get(self, request, job_id):
        """Given a job id, return a new instance of the relevant challenge for this user."""
        return FormattedResponse(client.request_reset(request.user.pk, job_id))


class ListJobsView(APIView):
    """Endpoint for listing the jobs on the andromeda host."""

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_view_jobs"

    def get(self, request):
        """Return a list of all jobs that have been submitted to an andromeda host."""
        return FormattedResponse(client.list_jobs())


class RestartJobView(APIView):
    """Endpoint for restarting a job on the andromeda host."""

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_manage_jobs"

    def post(self, request):
        """Given a job id, restart all instances of that challenge on the andromeda host."""
        return FormattedResponse(client.restart_job(request.data["job_id"]))


class ListInstancesView(APIView):
    """Endpoint for listing all instances of challenges on the andromeda host."""

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_view_jobs"

    def get(self, request):
        """Get a list of all challenge instances on the andromeda host."""
        return FormattedResponse(client.list_instances())


class SysinfoView(APIView):
    """Endpoint for getting the system info of an andromeda host."""

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_view_sysinfo"

    def get(self, request):
        """Get the reported system info(free ram, cpu, etc) of the andromeda host."""
        return FormattedResponse(client.sysinfo())


class JobSubmitView(APIView):
    """Endpoint to submit a job to the andromeda host and link it to a given challenge."""

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_manage_jobs"

    def post(self, request):
        """Submit a job to the andromeda host then add it to the challenge's challenge_metadata."""
        serializer = JobSubmitSerializer(request.data)
        challenge = get_object_or_404(Challenge.objects, id=serializer.data["challenge_id"])
        response = client.submit_job(serializer.data["job_spec"])
        challenge.challenge_metadata["cserv_name"] = response["id"]
        challenge.save()
        return FormattedResponse()


class JobSubmitRawView(APIView):
    """Endpoint to submit a job to the andromeda host."""

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_manage_jobs"

    def post(self, request):
        """Submit a job to the andromeda host."""
        serializer = JobSubmitRawSerializer(request.data)
        response = client.submit_job(serializer.data["job_spec"])
        return FormattedResponse(response)
