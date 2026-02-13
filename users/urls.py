from django.urls import path

from .views import CheckEmailView, CheckUsernameView, CsrfView, LoginView, LogoutView, MeView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('csrf/', CsrfView.as_view()),
    path('me/', MeView.as_view()),
    path('check-username/', CheckUsernameView.as_view()),
    path('check-email/', CheckEmailView.as_view()),
]
