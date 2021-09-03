"""URL routes for the challenge app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from challenges import views

router = DefaultRouter()
router.register(r"categories", views.CategoryViewset, basename="categories")
router.register(r"files", views.FileViewSet, basename="files")
router.register(r"tags", views.TagViewSet, basename="tags")
router.register(r"scores", views.ScoresViewset, basename="scores")
router.register(r"", views.ChallengeViewset, basename="challenges")

urlpatterns = [
    path("submit_flag/", views.FlagSubmitView.as_view(), name="submit-flag"),
    path("check_flag/", views.FlagCheckView.as_view(), name="check-flag"),
    path("feedback/", views.ChallengeFeedbackView.as_view(), name="submit-feedback"),
    path("vote/", views.ChallengeVoteView.as_view(), name="vote"),
    path("", include(router.urls)),
]
