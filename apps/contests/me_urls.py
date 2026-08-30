from django.urls import path

from apps.submissions.urls import me_urlpatterns as submission_urlpatterns

from .views import NotifySubscribeView

urlpatterns = [
    path("notify/", NotifySubscribeView.as_view(), name="notify-subscribe"),
    *submission_urlpatterns,
]
