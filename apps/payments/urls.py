from django.urls import path

from .views import (
    AdminPaymentDecisionView,
    AdminPaymentListView,
    ParticipationView,
    ReceiptViaBotView,
    UploadReceiptView,
)

contest_urlpatterns = [
    path("<slug:slug>/participation/", ParticipationView.as_view(), name="participation"),
    path("<slug:slug>/participation/receipt/", UploadReceiptView.as_view(), name="upload-receipt"),
    path("<slug:slug>/participation/via-bot/", ReceiptViaBotView.as_view(), name="receipt-via-bot"),
]

admin_urlpatterns = [
    path("payments/", AdminPaymentListView.as_view(), name="admin-payment-list"),
    path(
        "payments/<int:pk>/decision/",
        AdminPaymentDecisionView.as_view(),
        name="admin-payment-decision",
    ),
]
