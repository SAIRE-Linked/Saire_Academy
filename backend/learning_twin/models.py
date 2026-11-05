"""Skills assessed by mapped, instructor-reviewed ProofLoop assignments.

Neither local self-reported tests nor AI chat should ever become competency evidence.
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Skill(models.Model):
    FOUNDATIONS = 'foundations'
    ENGINEERING = 'engineering'
    AI = 'ai'
    CATEGORIES = [
        (FOUNDATIONS, 'Programming fundamentals'),
        (ENGINEERING, 'Professional software engineering'),
        (AI, 'AI engineering'),
    ]

    slug = models.SlugField(max_length=90, unique=True)
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORIES, default=FOUNDATIONS)
    position = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ('position', 'name')

    def __str__(self):
        return self.name


class AssignmentSkill(models.Model):
    """Instructor-defined mapping of one assignment rubric dimension to a skill."""
    TESTS = 'tests'
    DEFENCE = 'defence'
    QUALITY = 'quality'
    DIMENSIONS = [
        (TESTS, 'Verified test results'),
        (DEFENCE, 'Instructor code defence'),
        (QUALITY, 'Instructor code quality'),
    ]

    assignment = models.ForeignKey('assessments.Assignment', on_delete=models.PROTECT, related_name='skill_mappings')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='assignment_mappings')
    dimension = models.CharField(max_length=12, choices=DIMENSIONS)
    weight = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        ordering = ('assignment__slug', 'skill__position', 'dimension')
        constraints = [models.UniqueConstraint(fields=('assignment', 'skill', 'dimension'), name='unique_assignment_skill_dimension')]

    def __str__(self):
        return f'{self.assignment.slug} → {self.skill.name} ({self.get_dimension_display()})'
