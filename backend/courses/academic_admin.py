"""Private source provenance and authorable pathway structure."""
from django.contrib import admin
from .models import LearningPathway, PathwayUnit, ModulePrerequisite, SourceReference, SourceCoverage


class UnitInline(admin.TabularInline):
    model = PathwayUnit
    extra = 0
    autocomplete_fields = ['module']


@admin.register(LearningPathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'published']
    search_fields = ['title', 'slug']
    inlines = [UnitInline]


@admin.register(ModulePrerequisite)
class PrerequisiteAdmin(admin.ModelAdmin):
    list_display = ['module', 'required_module']
    autocomplete_fields = ['module', 'required_module']


class CoverageInline(admin.TabularInline):
    model = SourceCoverage
    extra = 0
    autocomplete_fields = ['module']


@admin.register(SourceReference)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'availability', 'pages']
    list_filter = ['availability']
    search_fields = ['code', 'title', 'attribution']
    inlines = [CoverageInline]
