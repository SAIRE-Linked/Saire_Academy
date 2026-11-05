from django.urls import path
from .api import my_learning_twin

urlpatterns = [path('learning-twin/me/', my_learning_twin, name='learning-twin-me')]
