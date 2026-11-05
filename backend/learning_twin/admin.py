"""Staff can define which project rubric dimensions support each skill."""
from django.contrib import admin
from .models import Skill, AssignmentSkill


class SkillMappingInline(admin.TabularInline):
    model = AssignmentSkill
    extra = 0
    autocomplete_fields = ('assignment',)
    fields = ('assignment', 'dimension', 'weight')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'position', 'active')
    list_filter = ('category', 'active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (SkillMappingInline,)


@admin.register(AssignmentSkill)
class AssignmentSkillAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'skill', 'dimension', 'weight')
    list_filter = ('dimension', 'skill__category')
    search_fields = ('assignment__title', 'skill__name')
    autocomplete_fields = ('assignment', 'skill')
