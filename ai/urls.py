from django.urls import path

from .views import (
    ParseInputView,
    NormalizeEventView,
    ScheduleEventsView,
    ParseNormalizeScheduleView,
    AiDataStashView,
)

urlpatterns = [
    path('parse/', ParseInputView.as_view(), name='parse'),
    path('normalize/', NormalizeEventView.as_view(), name='normalize'),
    path('schedule/', ScheduleEventsView.as_view(), name='schedule'),
    path('process/', ParseNormalizeScheduleView.as_view(), name='process'),
    path('stash/', AiDataStashView.as_view(), name='stash'),
    path('stash/<str:key>/', AiDataStashView.as_view(), name='stash_get'),
]
