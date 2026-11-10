from django.conf import settings
from django.db import models


class LessonIteration(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.PROTECT)
    started_at = models.DateTimeField()
    due_at = models.DateTimeField()
    supplementary_started_at = models.DateTimeField(null=True, blank=True)
    supplementary_due_at = models.DateTimeField(null=True, blank=True)
    primary_failed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    raw_score = models.PositiveSmallIntegerField(null=True, blank=True)
    credited_score = models.PositiveSmallIntegerField(null=True, blank=True)
    grade_cap = models.PositiveSmallIntegerField(default=70)
    quiz_submissions = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=24, default='active', choices=[
        (x, x.replace('_', ' ').title()) for x in
        ['active', 'failed', 'supplementary', 'exhausted', 'passed']])

    class Meta:
        constraints = [models.UniqueConstraint(fields=['learner', 'lesson'], name='unique_learner_lesson_iteration')]



class OrientationAcknowledgment(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    version = models.CharField(max_length=60)
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['learner', 'version'], name='one_acknowledgment_per_version')]


class SetupCompletion(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    guide = models.ForeignKey('courses.ModuleGuide', on_delete=models.CASCADE)
    revision = models.PositiveSmallIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['learner', 'guide', 'revision'], name='one_setup_completion_per_revision')]


class FormativeCheck(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE)
    stage = models.CharField(max_length=6, choices=[('before', 'Before'), ('after', 'After')])
    correct = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()
    checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['learner', 'lesson', 'stage'], name='one_formative_check_per_stage')]


class MistakeNote(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    mistake = models.TextField()
    correction = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-pk']
