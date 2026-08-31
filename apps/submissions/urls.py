"""Маршруты заявок в трёх группах: контест, свой профиль, админка."""

from django.urls import path

from .views import (
    AdminRescreenView,
    AdminSubmissionDetailView,
    AdminSubmissionListView,
    MySubmissionListView,
    MySubmissionView,
    PublicProfileView,
    SubmitSolutionView,
)

contest_urlpatterns = [
    path("<slug:slug>/submission/", MySubmissionView.as_view(), name="my-submission"),
    path("<slug:slug>/submission/submit/", SubmitSolutionView.as_view(), name="submit-solution"),
]

me_urlpatterns = [
    path("submissions/", MySubmissionListView.as_view(), name="my-submission-list"),
]

public_urlpatterns = [
    path("<str:username>/", PublicProfileView.as_view(), name="public-profile"),
]

admin_urlpatterns = [
    path("submissions/", AdminSubmissionListView.as_view(), name="admin-submission-list"),
    path(
        "submissions/<int:pk>/",
        AdminSubmissionDetailView.as_view(),
        name="admin-submission-detail",
    ),
    path(
        "submissions/<int:pk>/screen/",
        AdminRescreenView.as_view(),
        name="admin-submission-screen",
    ),
]
