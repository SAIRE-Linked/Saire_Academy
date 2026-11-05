"""Fill the missing checks on the original self-paced foundation lessons."""
import json
from pathlib import Path
from django.db import migrations

CHECKS_FILE = Path(__file__).resolve().parents[2] / 'content' / 'foundations_checks_v102.json'


def add_foundation_checks(apps, schema_editor):
    Lesson = apps.get_model('courses', 'Lesson')
    Question = apps.get_model('courses', 'QuizQuestion')
    database = schema_editor.connection.alias
    checks = json.loads(CHECKS_FILE.read_text(encoding='utf-8-sig'))
    lessons = Lesson.objects.using(database).filter(
        module__course__slug='ai-engineer-agentic-systems',
        public_id__in=checks,
        passing_score=0,
        quiz_questions__isnull=True,
    )
    for lesson in lessons:
        Question.objects.using(database).bulk_create([
            Question(
                lesson_id=lesson.pk, position=position, question=row['question'],
                option_a=row['answers'][0], option_b=row['answers'][1],
                option_c=row['answers'][2], option_d=row['answers'][3],
                correct=row['correct'], reason=row['reason'],
            )
            for position, row in enumerate(checks[lesson.public_id], start=1)
        ])


class Migration(migrations.Migration):
    dependencies = [('courses', '0001_initial')]
    operations = [migrations.RunPython(add_foundation_checks, migrations.RunPython.noop)]
