from django.urls import path

from apps.payments.urls import contest_urlpatterns as payment_urlpatterns
from apps.submissions.urls import contest_urlpatterns as submission_urlpatterns

from .views import ContestDetailView, ContestListView, FeaturedContestView

urlpatterns = [
    path("", ContestListView.as_view(), name="contest-list"),
    path("featured/", FeaturedContestView.as_view(), name="contest-featured"),
    # Маршруты заявок объявлены раньше, чем <slug>/, иначе "featured" и
    # "submission" перехватывались бы как слаг контеста.
    *submission_urlpatterns,
    *payment_urlpatterns,
    path("<slug:slug>/", ContestDetailView.as_view(), name="contest-detail"),
]
