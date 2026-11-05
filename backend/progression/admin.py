from django.contrib import admin
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import LessonIteration
from .services import credit


@admin.register(LessonIteration)
class IterationAdmin(admin.ModelAdmin):
    list_display = ['learner', 'lesson', 'status', 'due_at', 'credited_score']
    list_filter = ['status']
    readonly_fields = [f.name for f in LessonIteration._meta.fields]
    actions = ['sign_off']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description='Sign off active lessons without quizzes (100 raw; supplementary cap applies)')
    def sign_off(self, request, queryset):
        from rest_framework.exceptions import PermissionDenied
        for item in queryset:
            if item.lesson.quiz_questions.exists():
                continue
            with transaction.atomic():
                get_user_model().objects.select_for_update().get(pk=item.learner_id)
                item = LessonIteration.objects.select_for_update().get(pk=item.pk)
                try:
                    credit(item, 100, True)
                except PermissionDenied:
                    self.message_user(request, f'{item.lesson}: no active attempt', level='warning')
