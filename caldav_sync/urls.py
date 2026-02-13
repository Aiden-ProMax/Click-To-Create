from django.urls import path

from .views import CalDAVLinkView, SyncEventView

urlpatterns = [
    path('sync/', SyncEventView.as_view()),
    path('link/', CalDAVLinkView.as_view()),
]
