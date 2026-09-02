from django.urls import path

from apps.analytics.urls import admin_urlpatterns as analytics_urlpatterns
from apps.payments.urls import admin_urlpatterns as payment_urlpatterns
from apps.submissions.urls import admin_urlpatterns as submission_urlpatterns
from apps.users.admin_urls import urlpatterns as user_urlpatterns

from .views import AdminContestDetailView, AdminContestListCreateView, AdminContestPublishView

urlpatterns = [
    path("contests/", AdminContestListCreateView.as_view(), name="admin-contest-list"),
    path("contests/<int:pk>/", AdminContestDetailView.as_view(), name="admin-contest-detail"),
    path(
        "contests/<int:pk>/publish/",
        AdminContestPublishView.as_view(),
        name="admin-contest-publish",
    ),
    *submission_urlpatterns,
    *user_urlpatterns,
    *payment_urlpatterns,
    *analytics_urlpatterns,
]
