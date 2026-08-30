from django.urls import path

from .views import AdminContestDetailView, AdminContestListCreateView, AdminContestPublishView

urlpatterns = [
    path("contests/", AdminContestListCreateView.as_view(), name="admin-contest-list"),
    path("contests/<int:pk>/", AdminContestDetailView.as_view(), name="admin-contest-detail"),
    path(
        "contests/<int:pk>/publish/",
        AdminContestPublishView.as_view(),
        name="admin-contest-publish",
    ),
]
