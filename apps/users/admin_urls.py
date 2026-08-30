from django.urls import path

from .admin_views import AdminStatsView, AdminUserListView

urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
]
