from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import Course, Module, Lesson, Project
from .serializers import CourseSummarySerializer, course_payload


def catalogue_queryset(user=None):
    from progression.services import admin_access
    qs = Course.objects.all() if user is not None and admin_access(user) else Course.objects.filter(status="published")
    return qs.prefetch_related(
        Prefetch("modules", queryset=Module.objects.prefetch_related("lessons")),
    )


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "saire-learning-api"})


@api_view(["GET"])
@permission_classes([AllowAny])
def course_list(request):
    return Response(CourseSummarySerializer(catalogue_queryset(request.user), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def course_detail(request, slug):
    module_query = Module.objects.select_related("guide").order_by("position", "pk").prefetch_related(
        "topics",
        Prefetch("lessons", queryset=Lesson.objects.order_by("position", "pk").prefetch_related("sections", "quiz_questions")),
        Prefetch("projects", queryset=Project.objects.order_by("position", "pk")),
    )
    from progression.services import admin_access
    qs = Course.objects.all() if admin_access(request.user) else Course.objects.filter(status="published")
    course = qs.filter(slug=slug).prefetch_related(
        Prefetch("modules", queryset=module_query)
    ).first()
    if not course:
        raise NotFound("Course not found")
    return Response(course_payload(course, request.user))
