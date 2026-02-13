from django.urls import path

from .views import (
    GoogleEventSyncView,
    GoogleOAuthCallbackView,
    GoogleOAuthStartView,
    GoogleOAuthStatusView,
    GoogleOAuthDisconnectView,
)

urlpatterns = [
    path('oauth/google/start/', GoogleOAuthStartView.as_view()),
    path('oauth/google/callback', GoogleOAuthCallbackView.as_view()),
    path('api/google/events/sync/', GoogleEventSyncView.as_view()),
    path('api/google/status/', GoogleOAuthStatusView.as_view()),
    path('api/google/disconnect/', GoogleOAuthDisconnectView.as_view()),
]
