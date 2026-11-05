from django.urls import path
from . import api

urlpatterns = [
    path('auth/csrf/', api.csrf), path('auth/session-logout/', api.logout),
    path('dashboard/', api.dashboard), path('lessons/<slug:public_id>/', api.detail),
    path('lessons/<slug:public_id>/<str:action>/', api.action),
]
