"""Load the existing SAIRE-Linked curriculum into Django, without overwriting edits."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import Course, Module, Topic, Lesson, LessonSection, QuizQuestion, Project

SEED = Path(__file__).resolve().parents[3] / "content" / "ai_engineering_seed.json"


class Command(BaseCommand):
    help = "Load the original AI Engineering course. Existing courses are NOT modified."

    def handle(self, *args, **options):
        data = json.loads(SEED.read_text(encoding="utf-8"))
        with transaction.atomic():
            if Course.objects.filter(slug=data["slug"]).exists():
                self.stdout.write(self.style.WARNING(
                    f"Course '{data['slug']}' already exists; keeping your admin edits intact."
                ))
                return
            course = Course.objects.create(
                slug=data["slug"], title=data["title"], subtitle=data["subtitle"],
                description=data["description"], estimated_months=data["estimated_months"],
                status="published", featured=True,
            )
            modules = {}
            for item in data["phases"]:
                module = Module.objects.create(
                    course=course, position=item["id"], name=item["name"],
                    duration_weeks=item["duration"], category=item["category"],
                    icon=item["icon"], description=item["desc"], published=True,
                )
                modules[item["id"]] = module
                Topic.objects.bulk_create([
                    Topic(module=module, position=i, text=text)
                    for i, text in enumerate(item["topics"], start=1)
                ])
            for item in data["lessons"]:
                lesson = Lesson.objects.create(
                    module=modules[item["phaseId"]], public_id=item["id"],
                    position=len(Lesson.objects.filter(module=modules[item["phaseId"]])) + 1,
                    title=item["title"], minutes=item["minutes"],
                    difficulty=item["difficulty"], objective=item["objective"],
                    challenge=item["challenge"], published=True,
                )
                LessonSection.objects.bulk_create([
                    LessonSection(lesson=lesson, position=i, heading=section["heading"],
                                  body=section["body"], code=section.get("code", ""),
                                  language=section.get("language", "python"),
                                  note=section.get("note", ""))
                    for i, section in enumerate(item["sections"], start=1)
                ])
                if lesson.public_id == "p1-l1":
                    QuizQuestion.objects.bulk_create([
                        QuizQuestion(
                            lesson=lesson, position=i, question=q["question"],
                            option_a=q["answers"][0], option_b=q["answers"][1],
                            option_c=q["answers"][2], option_d=q["answers"][3],
                            correct=q["correct"], reason=q["reason"],
                        ) for i, q in enumerate(data["quiz"], start=1)
                    ])
            for item in data["projects"]:
                Project.objects.create(
                    module=modules[item["phase"]], public_id=item["id"],
                    name=item["name"], description=item["description"],
                    level=item["level"], skills_csv=", ".join(item["skills"]),
                )
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {course.title}: {len(modules)} phases, {len(data['lessons'])} lessons, {len(data['projects'])} projects"
        ))
