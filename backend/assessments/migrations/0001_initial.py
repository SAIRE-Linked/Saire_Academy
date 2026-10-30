"""Initial ProofLoop tables. Kept separate from the original curriculum migration."""
import uuid
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(name='Assignment', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('slug', models.SlugField(max_length=120, unique=True)),
            ('title', models.CharField(max_length=180)),
            ('brief', models.TextField()),
            ('learning_outcomes', models.TextField(help_text='One outcome per line')),
            ('template_url', models.URLField(blank=True, help_text='Optional instructor-approved GitHub template URL')),
            ('starter_bundle', models.FileField(blank=True, upload_to='assignment_starters/', help_text='ZIP available only to learners who started this assignment')),
            ('test_command', models.CharField(default='python -m unittest discover -s tests -v', max_length=180)),
            ('duration_days', models.PositiveSmallIntegerField(default=7, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(90)])),
            ('late_penalty_per_day', models.PositiveSmallIntegerField(default=20, validators=[django.core.validators.MaxValueValidator(100)], help_text='Percentage points removed per 24-hour overdue period from deadline component only')),
            ('q1', models.CharField(max_length=400)),
            ('q2', models.CharField(max_length=400)),
            ('q3', models.CharField(max_length=400)),
            ('q4', models.CharField(max_length=400)),
            ('q5', models.CharField(max_length=400)),
            ('published', models.BooleanField(default=False)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('module', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='courses.module')),
            ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assignments', to='courses.project')),
        ], options={'ordering': ('module__position', 'title')}),
        migrations.CreateModel(name='AssignmentAttempt', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
            ('due_at', models.DateTimeField()),
            ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attempts', to='assessments.assignment')),
            ('learner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignment_attempts', to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ('-started_at',)}),
        migrations.CreateModel(name='Submission', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('repository_url', models.URLField(help_text='Canonical GitHub repository URL')),
            ('commit_sha', models.CharField(max_length=40)),
            ('submitted_at', models.DateTimeField(default=django.utils.timezone.now)),
            ('status', models.CharField(max_length=20, default='pending_review', choices=[('pending_review', 'Awaiting instructor review'), ('reviewed', 'Reviewed')])),
            ('local_tests_passed', models.PositiveIntegerField(default=0)),
            ('local_tests_failed', models.PositiveIntegerField(default=0)),
            ('local_tests_errors', models.PositiveIntegerField(default=0)),
            ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='submissions', to='assessments.assignmentattempt')),
        ], options={'ordering': ('-submitted_at',)}),
        migrations.CreateModel(name='CodeReview', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('verified_test_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
            ('code_quality_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
            ('q1_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
            ('q2_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
            ('q3_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
            ('q4_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
            ('q5_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
            ('feedback', models.TextField(blank=True)),
            ('reviewed_at', models.DateTimeField(default=django.utils.timezone.now)),
            ('final_score', models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)),
            ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='completed_reviews', to=settings.AUTH_USER_MODEL)),
            ('submission', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='review', to='assessments.submission')),
        ]),
        migrations.AddConstraint(model_name='assignmentattempt', constraint=models.UniqueConstraint(fields=('assignment', 'learner'), name='one_attempt_per_student_assignment')),
        migrations.AddConstraint(model_name='submission', constraint=models.UniqueConstraint(fields=('attempt', 'commit_sha'), name='unique_submission_sha_per_attempt')),
    ]
