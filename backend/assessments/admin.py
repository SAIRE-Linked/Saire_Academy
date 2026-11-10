"""ProofLoop instructor desk. Grades are entered by staff, never by learners."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from .models import Assignment, AssignmentAttempt, Submission, CodeReview, GradingJob
from django.utils import timezone
from datetime import timedelta


def submitted_defence(submission):
    defence = getattr(submission, 'defence', None)
    if defence is None or defence.submitted_at is None:
        return 'No written defence has been handed in.'
    return format_html_join(
        '',
        '<div><strong>{}</strong><p style="white-space: pre-wrap">{}</p></div>',
        zip(defence.questions, defence.answers),
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'module', 'duration_days', 'published')
    list_filter = ('published', 'module__course')
    search_fields = ('title', 'slug', 'brief')
    autocomplete_fields = ('module', 'project')
    readonly_fields = ('created_at',)
    fieldsets = [
        ('Curriculum', {'fields': ('module', 'project', 'slug', 'title', 'brief', 'learning_outcomes', 'published', 'module_pass_score')}),
        ('Starter and assessment', {'fields': ('starter_bundle', 'template_url', 'test_command', 'duration_days', 'late_penalty_per_day')}),
        ('Code defence (5 questions)', {'fields': ('q1', 'q2', 'q3', 'q4', 'q5')}),
        ('Metadata', {'fields': ('created_at',)}),
    ]


@admin.register(AssignmentAttempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('learner', 'assignment', 'started_at', 'due_at')
    list_filter = ('assignment',)
    search_fields = ('learner__username', 'assignment__title')
    readonly_fields = ('assignment', 'learner', 'started_at', 'due_at')
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'short_sha', 'status', 'submitted_at', 'late_days')
    list_filter = ('status', 'attempt__assignment')
    search_fields = ('commit_sha', 'attempt__learner__username')
    readonly_fields = ('attempt', 'repository_url', 'commit_sha', 'submitted_at', 'status',
                       'local_tests_passed', 'local_tests_failed', 'local_tests_errors', 'late_days',
                       'defence_evidence', 'review_link')

    @admin.display(description='Submitted code defence')
    def defence_evidence(self, obj):
        return submitted_defence(obj)

    @admin.display(description='Instructor review')
    def review_link(self, obj):
        review = getattr(obj, 'review', None)
        if review:
            url = reverse('admin:assessments_codereview_change', args=[review.pk])
            return format_html('<a href="{}">Open review</a>', url)
        url = reverse('admin:assessments_codereview_add')
        return format_html('<a href="{}?submission={}">Start review for this commit</a>', url, obj.pk)

    def short_sha(self, obj):
        return obj.commit_sha[:12]
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CodeReview)
class CodeReviewAdmin(admin.ModelAdmin):
    list_display = ('submission', 'reviewer', 'verified_test_score', 'code_quality_score', 'final_score', 'reviewed_at')
    list_filter = ('reviewer',)
    search_fields = ('submission__attempt__learner__username', 'submission__commit_sha')
    autocomplete_fields = ('submission',)
    readonly_fields = ('reviewer', 'final_score', 'reviewed_at', 'defence_evidence')
    fieldsets = [
        ('Submission', {'fields': ('submission', 'reviewer', 'reviewed_at')}),
        ('Instructor-verified results', {'fields': ('verified_test_score', 'code_quality_score')}),
        ('Five code-defence answers (0–10 each)', {'fields': ('defence_evidence', 'q1_score', 'q2_score', 'q3_score', 'q4_score', 'q5_score')}),
        ('Outcome', {'fields': ('feedback', 'final_score')}),
    ]
    @admin.display(description='Submitted code defence')
    def defence_evidence(self, obj):
        if obj is None:
            return 'Read the submitted answers on the submission record before entering marks.'
        return submitted_defence(obj.submission)

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if obj and getattr(getattr(obj.submission, 'grading_job', None), 'status', None) == GradingJob.COMPLETE:
            base.append('verified_test_score')
        return base

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.reviewer = request.user
        super().save_model(request, obj, form, change)


@admin.register(GradingJob)
class GradingJobAdmin(admin.ModelAdmin):
    list_display = ('submission', 'status', 'approved_by', 'approved_at',
                    'github_commit_verified', 'verified_test_score', 'completed_at')
    list_filter = ('status', 'github_commit_verified', 'submission__attempt__assignment')
    search_fields = ('submission__attempt__learner__username', 'submission__commit_sha', 'submission__repository_url')
    readonly_fields = ('submission', 'status', 'approved_by', 'approved_at', 'claim_token',
                       'claimed_at', 'completed_at', 'github_commit_verified',
                       'verified_test_score', 'tests_passed', 'tests_failed',
                       'tests_errors', 'execution_log', 'failure_reason', 'created_at')
    actions = ('approve_repository_for_grading', 'requeue_failed_job', 'recover_stale_running_job')

    @admin.action(description='Approve selected repositories and queue for isolated grading')
    def approve_repository_for_grading(self, request, queryset):
        if not request.user.has_perm('assessments.change_gradingjob'):
            self.message_user(request, 'You lack grading permission.', level='ERROR')
            return
        approved = 0
        for job in queryset.select_related('submission'):
            if job.status != GradingJob.WAITING:
                continue
            # Instructor must independently confirm this repository belongs to
            # the correct learner and that they can access the submitted commit.
            job.status = GradingJob.QUEUED
            job.approved_by = request.user
            job.approved_at = timezone.now()
            job.save(update_fields=['status', 'approved_by', 'approved_at'])
            approved += 1
        self.message_user(request, f'{approved} grading jobs approved. Confirm repository ownership before using this action.')

    @admin.action(description='Requeue failed grading jobs (review error first)')
    def requeue_failed_job(self, request, queryset):
        if not request.user.has_perm('assessments.change_gradingjob'):
            return
        count = 0
        for job in queryset:
            if job.status != GradingJob.ERROR or not job.approved_at:
                continue
            job.status = GradingJob.QUEUED
            job.claim_token = None
            job.failure_reason = ''
            job.save(update_fields=['status', 'claim_token', 'failure_reason'])
            count += 1
        self.message_user(request, f'{count} error jobs requeued.')

    @admin.action(description='Mark stalled running jobs as errors (after 15 minutes)')
    def recover_stale_running_job(self, request, queryset):
        if not request.user.has_perm('assessments.change_gradingjob'):
            return
        deadline = timezone.now() - timedelta(minutes=15)
        count = 0
        for job in queryset:
            if job.status != GradingJob.RUNNING or not job.claimed_at or job.claimed_at > deadline:
                continue
            job.status = GradingJob.ERROR
            job.claim_token = None
            job.failure_reason = 'Instructor marked stalled worker run for review'
            job.save(update_fields=['status', 'claim_token', 'failure_reason'])
            count += 1
        self.message_user(request, f'{count} stalled grading jobs marked as errors. Investigate before requeueing.')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
