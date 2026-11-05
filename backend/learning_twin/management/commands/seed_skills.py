"""Seed *original* SAIRE skills/mappings without overwriting instructor edits."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from assessments.models import Assignment
from learning_twin.models import Skill, AssignmentSkill

SKILLS = (
    ('python-fundamentals', 'Python fundamentals', 'Foundational Python and numerical logic', 'foundations'),
    ('input-validation', 'Input validation', 'Reasoning about valid and invalid user inputs', 'foundations'),
    ('problem-decomposition', 'Problem decomposition', 'Designing functions with clear responsibilities', 'foundations'),
    ('code-explanation', 'Code explanation', 'Explaining why code works and why choices were made', 'engineering'),
    ('maintainability', 'Code maintainability', 'Readable, organised, maintainable implementations', 'engineering'),
    ('debugging', 'Debugging', 'Finding, reproducing, and fixing unexpected behaviour', 'engineering'),
)
MAPPINGS = (
    ('python-fundamentals', AssignmentSkill.TESTS, 2),
    ('input-validation', AssignmentSkill.TESTS, 1),
    ('problem-decomposition', AssignmentSkill.DEFENCE, 1),
    ('code-explanation', AssignmentSkill.DEFENCE, 2),
    ('maintainability', AssignmentSkill.QUALITY, 2),
)


class Command(BaseCommand):
    help = 'Create the initial original SAIRE Learning Twin skill taxonomy and evidence links.'

    def handle(self, *args, **options):
        assignment = Assignment.objects.filter(slug='saire-quotation-engine').first()
        if assignment is None:
            raise CommandError('Run python manage.py seed_curriculum and seed_proofloop first.')
        with transaction.atomic():
            created_count = 0
            for position, (slug, name, description, category) in enumerate(SKILLS, 1):
                skill, created = Skill.objects.get_or_create(slug=slug, defaults={
                    'name': name, 'description': description, 'category': category,
                    'position': position, 'active': True,
                })
                created_count += int(created)
            mapping_count = 0
            for slug, dimension, weight in MAPPINGS:
                skill = Skill.objects.get(slug=slug)
                _, created = AssignmentSkill.objects.get_or_create(
                    assignment=assignment, skill=skill, dimension=dimension,
                    defaults={'weight': weight},
                )
                mapping_count += int(created)
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} skills and {mapping_count} mappings; existing admin edits preserved.'))
