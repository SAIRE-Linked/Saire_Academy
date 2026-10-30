"""Run: python manage.py test courses"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from .models import Course, Module, Lesson, LessonSection, Project, QuizQuestion, Topic


class PublishedCurriculumApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.course = Course.objects.create(title="Python Starter", slug="python-starter", status="published")
        cls.module = Module.objects.create(course=cls.course, name="Basics", position=1)
        Topic.objects.create(module=cls.module, text="Variables")
        cls.lesson = Lesson.objects.create(module=cls.module, title="Variables", position=1, published=True)
        LessonSection.objects.create(lesson=cls.lesson, heading="Intro", body="Names bind to objects")
        QuizQuestion.objects.create(lesson=cls.lesson, question="What is a variable?", option_a="Name", option_b="Disk", option_c="Server", option_d="Compiler", correct=0)
        Project.objects.create(module=cls.module, name="Small Project", skills_csv="Python, Git")
        Lesson.objects.create(module=cls.module, title="Unreleased", published=False)
        cls.draft = Course.objects.create(title="Not live", slug="not-live", status="draft")

    def test_lists_published_courses_only(self):
        response = self.client.get("/api/v1/courses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["slug"] for item in response.json()], ["python-starter"])

    def test_course_payload_includes_editable_content_but_no_drafts(self):
        response = self.client.get("/api/v1/courses/python-starter/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["phases"][0]["topics"], ["Variables"])
        self.assertEqual(len(data["lessons"]), 1)
        self.assertEqual(data["lessons"][0]["sections"][0]["body"], "Names bind to objects")
        self.assertEqual(data["lessons"][0]["quiz"][0]["correct"], 0)
        self.assertEqual(data["projects"][0]["skills"], ["Python", "Git"])

    def test_unpublished_course_not_available(self):
        self.assertEqual(self.client.get("/api/v1/courses/not-live/").status_code, 404)

    def test_get_only_and_no_public_mutations(self):
        response = self.client.post("/api/v1/courses/", data={"title": "Attack"})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Course.objects.count(), 2)

    def test_unpublished_module_hidden(self):
        self.module.published = False
        self.module.save()
        data = self.client.get("/api/v1/courses/python-starter/").json()
        self.assertEqual(data["phases"], [])
        self.assertEqual(data["lessons"], [])

    def test_editor_changes_reflected_in_api(self):
        self.lesson.title = "New lesson title"
        self.lesson.save()
        response = self.client.get("/api/v1/courses/python-starter/")
        self.assertEqual(response.json()["lessons"][0]["title"], "New lesson title")


class SeedTests(TestCase):
    def test_initial_seed_is_complete_and_idempotent(self):
        call_command("seed_curriculum", verbosity=0)
        course = Course.objects.get(slug="ai-engineer-agentic-systems")
        self.assertEqual(course.modules.count(), 12)
        self.assertEqual(Topic.objects.filter(module__course=course).count(), 72)
        self.assertEqual(Lesson.objects.filter(module__course=course).count(), 4)
        self.assertEqual(Project.objects.filter(module__course=course).count(), 12)
        lesson = Lesson.objects.get(public_id="p1-l1")
        lesson.title = "My admin update"
        lesson.save()
        call_command("seed_curriculum", verbosity=0)
        self.assertEqual(Lesson.objects.get(public_id="p1-l1").title, "My admin update")
