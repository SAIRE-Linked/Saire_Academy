"""Isolated grading queue; no existing submissions or reviews are modified."""
import uuid
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('assessments', '0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='GradingJob', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('status', models.CharField(max_length=24, choices=[('awaiting_approval', 'Instructor repo approval required'), ('queued', 'Ready for isolated grader'), ('running', 'Grading in progress'), ('complete', 'Independently graded'), ('error', 'Infrastructure or verification error')], default='awaiting_approval', db_index=True)),
            ('approved_at', models.DateTimeField(blank=True, null=True)),
            ('claim_token', models.UUIDField(blank=True, editable=False, null=True)),
            ('claimed_at', models.DateTimeField(blank=True, null=True)),
            ('completed_at', models.DateTimeField(blank=True, null=True)),
            ('github_commit_verified', models.BooleanField(default=False)),
            ('verified_test_score', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
            ('tests_passed', models.PositiveSmallIntegerField(default=0)),
            ('tests_failed', models.PositiveSmallIntegerField(default=0)),
            ('tests_errors', models.PositiveSmallIntegerField(default=0)),
            ('execution_log', models.TextField(blank=True)),
            ('failure_reason', models.CharField(blank=True, max_length=300)),
            ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='approved_grading_jobs', to=settings.AUTH_USER_MODEL)),
            ('submission', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='grading_job', to='assessments.submission')),
        ], options={'ordering': ('-created_at',)}),
    ]
