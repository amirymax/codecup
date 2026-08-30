from django.urls import path

from .views import NotifySubscribeView

urlpatterns = [
    path("notify/", NotifySubscribeView.as_view(), name="notify-subscribe"),
]
