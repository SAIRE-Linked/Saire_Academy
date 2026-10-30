"""ProofLoop assessment records. Never execute learner code in this Django process."""
import uuid
import math
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

SCORE = [MinValueValidator(0), MaxValueValidator(100)]
TEN = [MinValueValidator(0), MaxValueValidator(10)]


class Assignment(models.Model):
    module = models.ForeignKey('courses.Module', related_name='assignments', on_delete=models.PROTECT)
    project = models.ForeignKey('courses.Project', related_name='assignments', on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=180)
    brief = models.TextField()
    learning_outcomes = models.TextField(help_text='One outcome per line')
    template_url = models.URLField(help_text='Optional instructor-approved GitHub template URL', blank=True)
    starter_bundle = models.FileField(upload_to='assignment_starters/', blank=True, help_text='ZIP available only to learners who started this assignment')
    test_command = models.CharField(max_length=180, default='python -m unittest discover -s tests -v')
    duration_days = models.PositiveSmallIntegerField(default=7, validators=[MinValueValidator(1), MaxValueValidator(90)])
    late_penalty_per_day = models.PositiveSmallIntegerField(default=20, validators=[MaxValueValidator(100)], help_text='Percentage points removed per 24-hour overdue period from deadline component only')
    q1 = models.CharField(max_length=400)
    q2 = models.CharField(max_length=400)
    q3 = models.CharField(max_length=400)
    q4 = models.CharField(max_length=400)
    q5 = models.CharField(max_length=400)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('module__position', 'title')

    def __str__(self):
        return self.title

    @property
    def questions(self):
        return [self.q1, self.q2, self.q3, self.q4, self.q5]


class AssignmentAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, related_name='attempts', on_delete=models.PROTECT)
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assignment_attempts', on_delete=models.PROTECT)
    started_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=('assignment', 'learner'), name='one_attempt_per_student_assignment')]
        ordering = ('-started_at',)

    def __str__(self):
        return f'{self.learner} / {self.assignment}'


class Submission(models.Model):
    REVIEW_PENDING = 'pending_review'
    REVIEWED = 'reviewed'
    STATUS = [(REVIEW_PENDING, 'Awaiting instructor review'), (REVIEWED, 'Reviewed')]
    attempt = models.ForeignKey(AssignmentAttempt, related_name='submissions', on_delete=models.PROTECT)
    repository_url = models.URLField(help_text='Canonical GitHub repository URL')
    commit_sha = models.CharField(max_length=40)
    submitted_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS, default=REVIEW_PENDING)
    # Local CLI tests are self-reported, never treated as independently verified grading evidence.
    local_tests_passed = models.PositiveIntegerField(default=0)
    local_tests_failed = models.PositiveIntegerField(default=0)
    local_tests_errors = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-submitted_at',)
        constraints = [models.UniqueConstraint(fields=('attempt', 'commit_sha'), name='unique_submission_sha_per_attempt')]

    @property
    def late_days(self):
        elapsed = self.submitted_at - self.attempt.due_at
        if elapsed.total_seconds() <= 0:
            return 0
        return math.ceil(elapsed.total_seconds() / 86400)

    def __str__(self):
        return f'{self.attempt} @ {self.commit_sha[:12]}'


class CodeReview(models.Model):
    submission = models.OneToOneField(Submission, related_name='review', on_delete=models.PROTECT)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='completed_reviews')
    # Only a human instructor may enter verified test results in this MVP.
    verified_test_score = models.PositiveSmallIntegerField(validators=SCORE)
    code_quality_score = models.PositiveSmallIntegerField(validators=SCORE)
    q1_score = models.PositiveSmallIntegerField(validators=TEN)
    q2_score = models.PositiveSmallIntegerField(validators=TEN)
    q3_score = models.PositiveSmallIntegerField(validators=TEN)
    q4_score = models.PositiveSmallIntegerField(validators=TEN)
    q5_score = models.PositiveSmallIntegerField(validators=TEN)
    feedback = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(default=timezone.now)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)

    def calculate_final_score(self):
        from decimal import Decimal, ROUND_HALF_UP
        # 50% trusted correctness + 30% five-question code defence
        # + 10% code quality + 10% deadline compliance.
        review_out_of_50 = sum([self.q1_score, self.q2_score, self.q3_score, self.q4_score, self.q5_score])
        late = self.submission.late_days
        deadline = max(0, 100 - (late * self.submission.attempt.assignment.late_penalty_per_day))
        total = (
            Decimal(self.verified_test_score) * Decimal('0.50') +
            Decimal(review_out_of_50) * Decimal('0.60') +
            Decimal(self.code_quality_score) * Decimal('0.10') +
            Decimal(deadline) * Decimal('0.10')
        )
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        from django.db import transaction
        self.full_clean()
        self.final_score = self.calculate_final_score()
        with transaction.atomic():
            super().save(*args, **kwargs)
            Submission.objects.filter(pk=self.submission_id).update(status=Submission.REVIEWED)

    def __str__(self):
        return f'{self.submission} · {self.final_score}%'
