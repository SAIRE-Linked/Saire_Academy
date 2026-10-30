"""ProofLoop instructor desk. Grades are entered by staff, never by learners."""
from django.contrib import admin
from .models import Assignment, AssignmentAttempt, Submission, CodeReview


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'module', 'duration_days', 'published')
    list_filter = ('published', 'module__course')
    search_fields = ('title', 'slug', 'brief')
    autocomplete_fields = ('module', 'project')
    readonly_fields = ('created_at',)
    fieldsets = [
        ('Curriculum', {'fields': ('module', 'project', 'slug', 'title', 'brief', 'learning_outcomes', 'published')}),
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
                       'local_tests_passed', 'local_tests_failed', 'local_tests_errors', 'late_days')
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
    readonly_fields = ('reviewer', 'final_score', 'reviewed_at')
    fieldsets = [
        ('Submission', {'fields': ('submission', 'reviewer', 'reviewed_at')}),
        ('Instructor-verified results', {'fields': ('verified_test_score', 'code_quality_score')}),
        ('Five code-defence answers (0–10 each)', {'fields': ('q1_score', 'q2_score', 'q3_score', 'q4_score', 'q5_score')}),
        ('Outcome', {'fields': ('feedback', 'final_score')}),
    ]
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.reviewer = request.user
        super().save_model(request, obj, form, change)
