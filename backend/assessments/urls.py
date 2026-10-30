from django.urls import path
from . import api

urlpatterns = [
    path('auth/login/', api.login, name='proofloop-login'),
    path('auth/logout/', api.logout, name='proofloop-logout'),
    path('auth/me/', api.me, name='proofloop-me'),
    path('assignments/', api.assignments, name='proofloop-assignments'),
    path('assignments/<slug:slug>/', api.assignment_detail, name='proofloop-assignment'),
    path('assignments/<slug:slug>/start/', api.start, name='proofloop-start'),
    path('assignments/<slug:slug>/mine/', api.my_attempt, name='proofloop-attempt'),
    path('assignments/<slug:slug>/starter/', api.starter, name='proofloop-starter'),
    path('assignments/<slug:slug>/submit/', api.submit, name='proofloop-submit'),
]
