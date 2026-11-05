from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('assessments', '0002_gradingjob')]
    operations = [
        migrations.CreateModel(
            name='MentorMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('learner', 'Learner'), ('mentor', 'Socratic Mentor')], max_length=10)),
                ('content', models.TextField(max_length=2400)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mentor_messages', to='assessments.assignment')),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saire_mentor_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('created_at', 'pk')},
        ),
        migrations.AddIndex(model_name='mentormessage', index=models.Index(fields=['learner', 'assignment', 'created_at'], name='mentor_owner_history_idx')),
    ]
