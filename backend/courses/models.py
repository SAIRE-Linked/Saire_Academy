"""Authorable curriculum models. All learner-facing content is public read-only."""
import uuid
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Course(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True, help_text="Stable URL identifier; avoid changing after publication.")
    subtitle = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    estimated_months = models.CharField(max_length=40, default="Flexible")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="draft")
    featured = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "title"]

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, related_name="modules", on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    duration_weeks = models.PositiveSmallIntegerField(default=1)
    category = models.CharField(max_length=32, default="foundations", help_text="Category key, e.g. foundations, intelligence, agents, applications, business.")
    icon = models.CharField(max_length=30, default="code")
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ["position", "id"]
        constraints = [models.UniqueConstraint(fields=["course", "position"], name="unique_module_position_per_course")]

    def __str__(self):
        return f"{self.course.title} · {self.position:02d} {self.name}"


class Topic(models.Model):
    module = models.ForeignKey(Module, related_name="topics", on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=1)
    text = models.CharField(max_length=400)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.text


class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name="lessons", on_delete=models.CASCADE)
    public_id = models.SlugField(max_length=130, unique=True, blank=True, help_text="Stable progress identifier. Leave blank to generate one; do not edit after release.")
    position = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=180)
    minutes = models.PositiveSmallIntegerField(default=30)
    difficulty = models.CharField(max_length=80, default="Fundamentals")
    objective = models.TextField(blank=True)
    challenge = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    passing_score = models.PositiveSmallIntegerField(default=0, help_text="0 = automatically use 75% of the questions.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module__position", "position", "id"]

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = f"lesson-{slugify(self.title)[:40]}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.module.name} · {self.title}"


class LessonSection(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="sections", on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=1)
    heading = models.CharField(max_length=180)
    body = models.TextField(blank=True, help_text="Plain text. Line breaks are preserved; no unsafe HTML is rendered.")
    code = models.TextField(blank=True)
    language = models.CharField(max_length=40, default="python", help_text="Code language label, e.g. Python, JavaScript, SQL, or Bash.")
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.heading


class QuizQuestion(models.Model):
    CHOICES = [(0, "A"), (1, "B"), (2, "C"), (3, "D")]
    lesson = models.ForeignKey(Lesson, related_name="quiz_questions", on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=1)
    question = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct = models.PositiveSmallIntegerField(choices=CHOICES)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Quiz: {self.question[:70]}"


class Project(models.Model):
    module = models.ForeignKey(Module, related_name="projects", on_delete=models.CASCADE)
    public_id = models.SlugField(max_length=130, unique=True, blank=True)
    position = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=180)
    level = models.CharField(max_length=80, default="Beginner")
    description = models.TextField(blank=True)
    skills_csv = models.CharField(max_length=350, blank=True, help_text="Comma-separated skill names, e.g. Python, SQL, Git")
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ["module__position", "position", "id"]

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = f"project-{slugify(self.name)[:40]}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
