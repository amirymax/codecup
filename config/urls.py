from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.views import ApiNotFoundView, HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/", include("apps.users.urls")),
    path("api/contests/", include("apps.contests.urls")),
    path("api/me/", include("apps.contests.me_urls")),
    path("api/admin/", include("apps.contests.admin_urls")),
    path("api/users/", include("apps.submissions.public_urls")),
    path("api/telegram/", include("apps.telegrambot.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # Должен идти последним: всё остальное под /api/ — это 404 в формате JSON.
    re_path(r"^api/", ApiNotFoundView.as_view()),
]
