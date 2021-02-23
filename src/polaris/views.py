from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView

from backend.response import FormattedResponse
from challenge.models import Challenge
from polaris import client


class GetInstanceView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_get"

    def get(self, request, challenge_id):
        return FormattedResponse(client.allocate_instance(challenge_id, request.user))


class ResetInstanceView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = "challenge_instance_reset"

    def get(self, request, challenge_id):
        return FormattedResponse(client.reallocate_instance(challenge_id, request.user))


class ChallengeViewset(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    throttle_scope = "polaris_challenges"

    def list(self, request):
        return FormattedResponse(client.list_challenges(request.GET.get('filter', '')))

    def retrieve(self, request, pk):
        return FormattedResponse(client.get_challenge(pk))

    def destroy(self, request, pk):
        return FormattedResponse(client.delete_challenge(pk))

    def create(self, request):
        challenge_id = request.GET.get('challenge_id', '')
        if challenge_id == '':
            return FormattedResponse(client.submit_challenge(request.data))
        challenge = get_object_or_404(Challenge.objects, challenge_id)
        response = client.submit_challenge(challenge)
        challenge.challenge_metadata['cserv_name'] = response.data['id']
        challenge.save()
        return response


class DeploymentViewset(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    throttle_scope = "polaris_deployments"

    def list(self, request):
        return FormattedResponse(client.list_deployments(request.GET.get('deploymentfilter', ''),
                                                         request.GET.get('challengefilter', '')))

    def retrieve(self, request, pk):
        return FormattedResponse(client.get_deployment(pk))

    def create(self, request):
        return FormattedResponse(client.submit_deployment(request.data))

    def destroy(self, request, pk):
        return FormattedResponse(client.delete_deployment(pk))


class HostViewset(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    throttle_scope = "polaris_hosts"

    def list(self, request):
        return FormattedResponse(client.list_hosts(request.GET.get('filter', '')))

    def retrieve(self, request, pk):
        return FormattedResponse(client.get_host(pk))


class ListInstancesView(APIView):
    permission_classes = (IsAdminUser,)
    throttle_scope = "polaris_view_instances"

    def get(self, request):
        return FormattedResponse(client.list_instances(request.GET.get('hostfilter', ''), request.GET.get('challengefilter', '')))
