"""Public API contracts shaped for the existing React LMS frontend."""
from django.db.models import Prefetch
from rest_framework import serializers
from .models import Course, Module, Lesson, Project


class CourseSummarySerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()
    phase_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("slug", "title", "subtitle", "description", "estimated_months", "phase_count", "lesson_count")

    def get_phase_count(self, obj):
        return sum(m.published for m in obj.modules.all())

    def get_lesson_count(self, obj):
        return sum(len([l for l in m.lessons.all() if l.published]) for m in obj.modules.all() if m.published)


def course_payload(course):
    """Never reveal drafts, even when they belong to a published parent."""
    phases, lessons, projects = [], [], []
    for module in course.modules.all():
        if not module.published:
            continue
        visible_projects = [project for project in module.projects.all() if project.published]
        phases.append({
            "id": module.position, "name": module.name, "duration": module.duration_weeks,
            "category": module.category, "desc": module.description, "icon": module.icon,
            "topics": [topic.text for topic in module.topics.all()],
            "project": visible_projects[0].name if visible_projects else "Project to be announced",
        })
        for lesson in module.lessons.all():
            if not lesson.published:
                continue
            questions = list(lesson.quiz_questions.all())
            lessons.append({
                "id": lesson.public_id, "phaseId": module.position,
                "title": lesson.title, "minutes": lesson.minutes, "difficulty": lesson.difficulty,
                "objective": lesson.objective, "challenge": lesson.challenge,
                "sections": [
                    {"heading": section.heading, "body": section.body,
                     "code": section.code, "language": section.language, "note": section.note}
                    for section in lesson.sections.all()
                ],
                "quiz": [{
                    "question": q.question,
                    "answers": [q.option_a, q.option_b, q.option_c, q.option_d],
                    "correct": q.correct, "reason": q.reason,
                } for q in questions],
                "passing_score": min(lesson.passing_score or (len(questions) * 3 + 3) // 4, len(questions)) if questions else 0,
            })
        for project in visible_projects:
            projects.append({
                "id": project.public_id, "name": project.name, "level": project.level,
                "phase": module.position, "description": project.description,
                "skills": [skill.strip() for skill in project.skills_csv.split(",") if skill.strip()],
            })
    return {
        "slug": course.slug, "title": course.title, "subtitle": course.subtitle,
        "description": course.description, "estimated_months": course.estimated_months,
        "updated_at": course.updated_at.isoformat(),
        "phases": phases, "lessons": lessons, "projects": projects,
    }
