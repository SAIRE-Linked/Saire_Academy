"""Authorable curriculum models. All learner-facing content is public read-only."""
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, URLValidator
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
    curriculum_key = models.SlugField(max_length=80, unique=True, null=True, blank=True, editable=False,
        help_text='Stable seed identity; module names and ordering remain editable.')
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


class ModuleGuide(models.Model):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='guide')
    title = models.CharField(max_length=180)
    introduction = models.TextField()
    outcomes = models.TextField(help_text='One outcome per line. Start with an action the learner can demonstrate.')
    published = models.BooleanField(default=False)
    required_setup = models.BooleanField(default=True)
    revision = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)],
                                                help_text='Increase when learners should redo the checklist.')
    first_program = models.BooleanField(default=False, help_text='This lab includes running a first program.')

    def __str__(self):
        return self.title


class SetupStep(models.Model):
    guide = models.ForeignKey(ModuleGuide, on_delete=models.CASCADE, related_name='steps')
    position = models.PositiveSmallIntegerField(default=1)
    heading = models.CharField(max_length=180)
    instructions = models.TextField()
    command = models.TextField(blank=True)
    verification = models.CharField(max_length=240, help_text='What the learner should confirm before ticking this step.')

    class Meta:
        ordering = ['position', 'pk']


class LessonGuide(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='guide')
    explanation = models.TextField()
    demonstration = models.TextField()
    example = models.TextField(blank=True, help_text='Optional plain-text code sample.')
    guided_exercise = models.TextField()
    independent_exercise = models.TextField()
    further_explanation = models.TextField(blank=True)

    def __str__(self):
        return str(self.lesson)


class LearningResource(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='learning_resources')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='learning_resources')
    title = models.CharField(max_length=180)
    url = models.URLField(validators=[URLValidator(schemes=['https'])])
    purpose = models.CharField(max_length=300)
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['position', 'pk']

    def clean(self):
        super().clean()
        if self.lesson_id and self.lesson.module_id != self.module_id:
            raise ValidationError({'lesson': 'Choose a lesson from this module.'})

    def __str__(self):
        return self.title


class GlossaryEntry(models.Model):
    term = models.CharField(max_length=100, unique=True)
    definition = models.TextField()
    example = models.TextField(blank=True)
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ['term']

    def __str__(self):
        return self.term


class FormativeQuestion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='formative_questions')
    position = models.PositiveSmallIntegerField(default=1)
    prompt = models.CharField(max_length=300)
    option_a = models.CharField(max_length=220)
    option_b = models.CharField(max_length=220)
    option_c = models.CharField(max_length=220)
    correct = models.PositiveSmallIntegerField(choices=[(0, 'A'), (1, 'B'), (2, 'C')])
    explanation = models.CharField(max_length=500)

    class Meta:
        ordering = ['position', 'pk']


class LearningPathway(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=180)
    description = models.TextField()
    disclaimer = models.CharField(max_length=400, blank=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class PathwayUnit(models.Model):
    pathway = models.ForeignKey(LearningPathway, related_name='units', on_delete=models.CASCADE)
    module = models.ForeignKey(Module, related_name='pathway_units', on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    year = models.PositiveSmallIntegerField(choices=[(1, 'Foundation year'), (2, 'Second year')], default=1)
    scope = models.TextField(help_text='State what is fully authored and what remains a backlog item.')
    shared = models.BooleanField(default=False, help_text='Public label for modules shared with another pathway.')

    class Meta:
        ordering = ['position', 'pk']
        constraints = [models.UniqueConstraint(fields=['pathway', 'position'], name='pathway_unique_position'),
                       models.UniqueConstraint(fields=['pathway', 'module'], name='pathway_unique_module')]

    def __str__(self):
        return f'{self.pathway}: {self.position}. {self.module.name}'


class ModulePrerequisite(models.Model):
    module = models.ForeignKey(Module, related_name='prerequisites', on_delete=models.CASCADE)
    required_module = models.ForeignKey(Module, related_name='required_by', on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['module', 'required_module'], name='unique_module_requirement'),
                       models.CheckConstraint(condition=~models.Q(module=models.F('required_module')), name='no_self_requirement')]

    def clean(self):
        super().clean()
        if not self.module_id or not self.required_module_id:
            return
        if self.module.course_id == self.required_module.course_id:
            raise ValidationError('Same-course order is already enforced. Use prerequisites only across courses.')
        # Course-level DAG makes cross-course progress recursion safe, including earlier modules.
        edges = list(type(self).objects.exclude(pk=self.pk).values_list('module__course_id', 'required_module__course_id'))
        edges.append((self.module.course_id, self.required_module.course_id))
        def reaches(start, target, seen):
            if start == target:
                return True
            if start in seen:
                return False
            return any(reaches(b, target, seen | {start}) for a, b in edges if a == start)
        if reaches(self.required_module.course_id, self.module.course_id, set()):
            raise ValidationError('This prerequisite would create a cycle between courses.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SourceReference(models.Model):
    """Internal bibliographic metadata only. Never include original files or excerpts."""
    code = models.CharField(max_length=80, unique=True)
    title = models.CharField(max_length=250)
    attribution = models.CharField(max_length=350, blank=True)
    availability = models.CharField(max_length=15, choices=[('audited', 'Available: topic audit'), ('missing', 'Awaiting source')])
    sha256 = models.CharField(max_length=64, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    audit_note = models.TextField(blank=True)

    def __str__(self):
        return f'{self.code}: {self.title}'


class SourceCoverage(models.Model):
    source = models.ForeignKey(SourceReference, related_name='coverage', on_delete=models.CASCADE)
    module = models.ForeignKey(Module, related_name='source_coverage', on_delete=models.PROTECT)
    topic = models.CharField(max_length=240, help_text='Paraphrased topic; never paste source passages.')
    page_range = models.CharField(max_length=80, blank=True, help_text='One-based PDF pages, not printed page numbers.')
    coverage = models.CharField(max_length=20, choices=[('partial', 'Partial original slice'), ('backlog', 'Not authored'), ('pending_source', 'Source validation pending')])
    gap = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['source', 'module', 'topic'], name='unique_source_topic_mapping')]
