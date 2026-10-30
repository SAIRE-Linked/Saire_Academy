"""One-time import of the original SAIRE Quotations assignment (no old WTC content)."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from assessments.models import Assignment
from courses.models import Module

# backend/assessments/management/commands/ -> repo/assignments/quotation-engine
STARTER = Path(__file__).resolve().parents[4] / 'assignments' / 'quotation-engine'


class Command(BaseCommand):
    help = 'Seed first original ProofLoop assignment without overwriting admin edits.'

    def handle(self, *args, **kwargs):
        module = Module.objects.filter(course__slug='ai-engineer-agentic-systems', position=1).first()
        if not module:
            raise CommandError('Run python manage.py seed_curriculum first.')
        with transaction.atomic():
            a, created = Assignment.objects.get_or_create(slug='saire-quotation-engine', defaults={
                'module': module, 'title': 'SAIRE Quotation Engine',
                'brief': 'Build a reusable Python quotation calculator for a digital services company. Validate inputs, use Decimal arithmetic, write regression tests, and explain your implementation.',
                'learning_outcomes': 'Write reusable Python functions\nValidate user and financial inputs\nUse Decimal for money\nWrite independent unit tests\nExplain design trade-offs',
                'duration_days': 7, 'published': True,
                'q1': 'Why is Decimal preferable to float for monetary values?',
                'q2': 'How does your implementation reject invalid input?',
                'q3': 'How did you break the problem into separate functions?',
                'q4': 'Show an edge-case regression test and explain it.',
                'q5': 'How would you redesign the engine for stacked discounts?',
            })
            if not created:
                self.stdout.write('Assignment already exists; keeping Django Admin edits intact.')
                return
            archive = BytesIO()
            with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
                for name in ('README.md', 'assignment.json', 'src/quotation.py', 'tests/test_quotation.py'):
                    z.write(STARTER / name, name)
            a.starter_bundle.save('saire-quotation-engine-starter.zip', ContentFile(archive.getvalue()), save=True)
        self.stdout.write(self.style.SUCCESS('Published SAIRE Quotation Engine with private starter ZIP.'))
