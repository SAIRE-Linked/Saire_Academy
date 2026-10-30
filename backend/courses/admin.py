"""Editor-friendly admin: courses -> modules -> topics, lessons and projects."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Course, Module, Topic, Lesson, LessonSection, QuizQuestion, Project


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ("position", "name", "duration_weeks", "category", "icon", "published")
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "featured", "position", "updated_at")
    list_filter = ("status", "featured")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("status", "featured", "position")
    inlines = [ModuleInline]
    fieldsets = (("Identity", {"fields": ("title", "slug", "subtitle", "description")}),
                 ("Publishing", {"fields": ("status", "featured", "position", "estimated_months")}))


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ("position", "text")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "position", "category", "published", "manage_lessons")
    list_filter = ("course", "category", "published")
    search_fields = ("name", "course__title")
    list_editable = ("position", "published")
    inlines = [TopicInline]
    autocomplete_fields = ("course",)

    @admin.display(description="Curriculum")
    def manage_lessons(self, obj):
        url = reverse("admin:courses_lesson_changelist")
        return format_html('<a href="{}?module__id__exact={}">Edit lessons</a>', url, obj.pk)


class SectionInline(admin.StackedInline):
    model = LessonSection
    extra = 1
    fields = ("position", "heading", "body", "code", "language", "note")


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 0
    fields = ("position", "question", ("option_a", "option_b"), ("option_c", "option_d"), "correct", "reason")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "position", "published", "minutes", "updated_at")
    list_filter = ("module__course", "module", "published", "difficulty")
    list_select_related = ("module", "module__course")
    search_fields = ("title", "public_id", "objective")
    list_editable = ("position", "published")
    readonly_fields = ("public_id", "updated_at")
    autocomplete_fields = ("module",)
    inlines = [SectionInline, QuizQuestionInline]
    fieldsets = (("Lesson", {"fields": ("module", "title", "position", "public_id")}),
                 ("Content", {"fields": ("objective", "challenge", "minutes", "difficulty")}),
                 ("Publishing & assessment", {"fields": ("published", "passing_score", "updated_at")}))


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "module", "position", "level", "published")
    list_filter = ("module__course", "published")
    list_editable = ("position", "published")
    search_fields = ("name",)
    autocomplete_fields = ("module",)
