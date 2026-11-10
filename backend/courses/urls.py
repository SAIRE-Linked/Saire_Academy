from django.urls import path
from .views import course_list, course_detail
from .pathways import pathway_list

urlpatterns = [
    path('pathways/', pathway_list, name='pathway-list'),
    path("courses/", course_list, name="course-list"),
    path("courses/<slug:slug>/", course_detail, name="course-detail"),
]
