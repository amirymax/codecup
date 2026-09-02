from django.urls import path

from .views import AdminAnalyticsView, TrackEventView

urlpatterns = [
    path("event/", TrackEventView.as_view(), name="track-event"),
]

admin_urlpatterns = [
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]
