import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('assessments', '0002_gradingjob')]
    operations = [
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=90, unique=True)),
                ('name', models.CharField(max_length=140)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(max_length=30, choices=[('foundations', 'Programming fundamentals'), ('engineering', 'Professional software engineering'), ('ai', 'AI engineering')], default='foundations')),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('active', models.BooleanField(default=True)),
            ], options={'ordering': ('position', 'name')},
        ),
        migrations.CreateModel(
            name='AssignmentSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dimension', models.CharField(max_length=12, choices=[('tests', 'Verified test results'), ('defence', 'Instructor code defence'), ('quality', 'Instructor code quality')])),
                ('weight', models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='skill_mappings', to='assessments.assignment')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_mappings', to='learning_twin.skill')),
            ], options={'ordering': ('assignment__slug', 'skill__position', 'dimension')},
        ),
        migrations.AddConstraint(
            model_name='assignmentskill',
            constraint=models.UniqueConstraint(fields=('assignment', 'skill', 'dimension'), name='unique_assignment_skill_dimension'),
        ),
    ]
