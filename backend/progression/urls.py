from django.urls import path
from . import academy_api, api

urlpatterns = [
    path('academy/orientation/', academy_api.orientation),
    path('academy/handbook/', academy_api.handbook),
    path('academy/modules/<int:module_id>/setup/', academy_api.setup),
    path('academy/lessons/<slug:public_id>/check/<str:stage>/', academy_api.formative),
    path('academy/notes/', academy_api.notes),
    path('academy/study-tools/', academy_api.study_tools),
    path('auth/csrf/', api.csrf), path('auth/session-logout/', api.logout),
    path('dashboard/', api.dashboard), path('lessons/<slug:public_id>/', api.detail),
    path('lessons/<slug:public_id>/<str:action>/', api.action),
]
