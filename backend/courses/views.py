from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import Course, Module, Lesson, Project
from .serializers import CourseSummarySerializer, course_payload


def catalogue_queryset():
    return Course.objects.filter(status="published").prefetch_related(
        Prefetch("modules", queryset=Module.objects.prefetch_related("lessons")),
    )


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "saire-learning-api"})


@api_view(["GET"])
@permission_classes([AllowAny])
def course_list(request):
    return Response(CourseSummarySerializer(catalogue_queryset(), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def course_detail(request, slug):
    module_query = Module.objects.order_by("position", "pk").prefetch_related(
        "topics",
        Prefetch("lessons", queryset=Lesson.objects.order_by("position", "pk").prefetch_related("sections", "quiz_questions")),
        Prefetch("projects", queryset=Project.objects.order_by("position", "pk")),
    )
    course = Course.objects.filter(status="published", slug=slug).prefetch_related(
        Prefetch("modules", queryset=module_query)
    ).first()
    if not course:
        raise NotFound("Course not found")
    return Response(course_payload(course))
