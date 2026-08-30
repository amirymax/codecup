from django.urls import path

from .views import (
    AuthLogoutView,
    AuthRefreshView,
    CurrentUserView,
    TelegramAuthExchangeView,
    TelegramAuthStartView,
    TelegramAuthStatusView,
)

urlpatterns = [
    path("telegram/start/", TelegramAuthStartView.as_view(), name="auth-telegram-start"),
    path("telegram/status/", TelegramAuthStatusView.as_view(), name="auth-telegram-status"),
    path("telegram/exchange/", TelegramAuthExchangeView.as_view(), name="auth-telegram-exchange"),
    path("refresh/", AuthRefreshView.as_view(), name="auth-refresh"),
    path("logout/", AuthLogoutView.as_view(), name="auth-logout"),
    path("me/", CurrentUserView.as_view(), name="auth-me"),
]
