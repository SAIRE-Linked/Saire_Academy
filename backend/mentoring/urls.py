from django.urls import path
from .api import mentor, status_view

urlpatterns = [
    path('mentor/status/', status_view, name='saire-mentor-status'),
    path('assignments/<slug:slug>/mentor/', mentor, name='saire-mentor'),
]
