from django.urls import path

from .views import ContestDetailView, ContestListView, FeaturedContestView

urlpatterns = [
    path("", ContestListView.as_view(), name="contest-list"),
    path("featured/", FeaturedContestView.as_view(), name="contest-featured"),
    path("<slug:slug>/", ContestDetailView.as_view(), name="contest-detail"),
]
