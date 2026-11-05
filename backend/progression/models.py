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

