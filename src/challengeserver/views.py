from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.schemas.openapi import AutoSchema

from backend.response import FormattedResponse
from challenge.models import Challenge
from challengeserver import client
from challengeserver.serializers import JobSubmitSerializer


class GetInstanceView(APIView):
    """
    Get a challenge instance.
    """
    schema = AutoSchema(tags=['challengeServer', 'challengeInstances'])

    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_get"

    def get(self, request, job_id):
        return FormattedResponse(
            client.get_instance(request.user.id, job_id)
        )


class ResetInstanceView(APIView):
    """
    'Reset' a challenge instance.
    """
    schema = AutoSchema(tags=['challengeServer', 'challengeInstances'])

    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_reset"

    def get(self, request, job_id):
        return FormattedResponse(
            client.request_reset(request.user.id, job_id)
        )


class ListJobsView(APIView):
    """
    List all jobs.
    """
    schema = AutoSchema(tags=['challengeServer', 'jobs'])

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_view_jobs"

    def get(self, request):
        return FormattedResponse(
            client.list_jobs()
        )


class RestartJobView(APIView):
    """
    Restart a job.
    """
    schema = AutoSchema(tags=['challengeServer', 'jobs'])

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_manage_jobs"

    def post(self, request):
        return FormattedResponse(
            client.restart_job(request.data["job_id"])
        )


class ListInstancesView(APIView):
    """
    List all challenge instances.
    """
    schema = AutoSchema(tags=['challengeServer', 'challengeInstances'])

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_view_jobs"

    def get(self, request):
        return FormattedResponse(
            client.list_instances()
        )


class SysinfoView(APIView):
    """
    Get system information of the Andromeda node.
    """
    schema = AutoSchema(operation_id_base='System', tags=['challengeServer'])

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_view_sysinfo"

    def get(self, request):
        return FormattedResponse(
            client.sysinfo()
        )


class JobSubmitView(APIView):
    """
    Create a new job.
    """
    schema = AutoSchema(tags=['challengeServer', 'jobs'])

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_manage_jobs"

    def post(self, request):
        serializer = JobSubmitSerializer(request.data)
        challenge = get_object_or_404(Challenge.objects, id=serializer.data['challenge_id'])
        response = client.submit_job(serializer.data['job_spec'])
        challenge.challenge_metadata['cserv_name'] = response['id']
        challenge.save()
        return FormattedResponse()


class JobSubmitRawView(APIView):
    """
    Create a new job.
    """
    schema = AutoSchema(tags=['challengeServer', 'jobs'])

    permission_classes = (IsAdminUser,)
    throttle_scope = "andromeda_manage_jobs"

    def post(self, request):
        serializer = JobSubmitSerializer(request.data)
        response = client.submit_job(serializer.data['job_spec'])
        return FormattedResponse(response)
