"""
URL configuration for autoplanner project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.page, {'template_name': 'index.html'}),
    path('index.html', views.page, {'template_name': 'index.html'}),
    path('login.html', views.page, {'template_name': 'login.html'}),
    path('dashboard.html', views.page, {'template_name': 'dashboard.html'}),
    path('connect_to_calendar.html', views.page, {'template_name': 'connect_to_calendar.html'}),
    path('add_plan_backend.html', views.page, {'template_name': 'add_plan_backend.html'}),
    path('confirmation.html', views.page, {'template_name': 'confirmation.html'}),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/events/', include('events.urls')),
    path('api/caldav/', include('caldav_sync.urls')),
    path('', include('google_sync.urls')),
    path('api/ai/', include('ai.urls')),
]
