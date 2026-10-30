# Initial authorable curriculum schema for SAIRE-Linked Digital Learning.
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="Course", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=180)),
            ("slug", models.SlugField(max_length=180, unique=True, help_text="Stable URL identifier; avoid changing after publication.")),
            ("subtitle", models.CharField(blank=True, max_length=250)),
            ("description", models.TextField(blank=True)),
            ("estimated_months", models.CharField(default="Flexible", max_length=40)),
            ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=12)),
            ("featured", models.BooleanField(default=False)),
            ("position", models.PositiveIntegerField(default=0)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
        ], options={"ordering": ["position", "title"]}),
        migrations.CreateModel(name="Module", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("position", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
            ("name", models.CharField(max_length=180)),
            ("description", models.TextField(blank=True)),
            ("duration_weeks", models.PositiveSmallIntegerField(default=1)),
            ("category", models.CharField(default="foundations", help_text="Category key, e.g. foundations, intelligence, agents, applications, business.", max_length=32)),
            ("icon", models.CharField(default="code", max_length=30)),
            ("published", models.BooleanField(default=True)),
            ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="modules", to="courses.course")),
        ], options={"ordering": ["position", "id"]}),
        migrations.CreateModel(name="Topic", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("position", models.PositiveSmallIntegerField(default=1)),
            ("text", models.CharField(max_length=400)),
            ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topics", to="courses.module")),
        ], options={"ordering": ["position", "id"]}),
        migrations.CreateModel(name="Lesson", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("public_id", models.SlugField(blank=True, help_text="Stable progress identifier. Leave blank to generate one; do not edit after release.", max_length=130, unique=True)),
            ("position", models.PositiveSmallIntegerField(default=1)),
            ("title", models.CharField(max_length=180)),
            ("minutes", models.PositiveSmallIntegerField(default=30)),
            ("difficulty", models.CharField(default="Fundamentals", max_length=80)),
            ("objective", models.TextField(blank=True)),
            ("challenge", models.TextField(blank=True)),
            ("published", models.BooleanField(default=False)),
            ("passing_score", models.PositiveSmallIntegerField(default=0, help_text="0 = automatically use 75% of the questions.")),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="courses.module")),
        ], options={"ordering": ["module__position", "position", "id"]}),
        migrations.CreateModel(name="LessonSection", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("position", models.PositiveSmallIntegerField(default=1)),
            ("heading", models.CharField(max_length=180)),
            ("body", models.TextField(blank=True, help_text="Plain text. Line breaks are preserved; no unsafe HTML is rendered.")),
            ("code", models.TextField(blank=True)),
            ("language", models.CharField(default="python", help_text="Code language label, e.g. Python, JavaScript, SQL, or Bash.", max_length=40)),
            ("note", models.TextField(blank=True)),
            ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="courses.lesson")),
        ], options={"ordering": ["position", "id"]}),
        migrations.CreateModel(name="QuizQuestion", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("position", models.PositiveSmallIntegerField(default=1)),
            ("question", models.TextField()),
            ("option_a", models.CharField(max_length=500)),
            ("option_b", models.CharField(max_length=500)),
            ("option_c", models.CharField(max_length=500)),
            ("option_d", models.CharField(max_length=500)),
            ("correct", models.PositiveSmallIntegerField(choices=[(0,"A"),(1,"B"),(2,"C"),(3,"D")])),
            ("reason", models.TextField(blank=True)),
            ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_questions", to="courses.lesson")),
        ], options={"ordering": ["position", "id"]}),
        migrations.CreateModel(name="Project", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("public_id", models.SlugField(blank=True, max_length=130, unique=True)),
            ("position", models.PositiveSmallIntegerField(default=1)),
            ("name", models.CharField(max_length=180)),
            ("level", models.CharField(default="Beginner", max_length=80)),
            ("description", models.TextField(blank=True)),
            ("skills_csv", models.CharField(blank=True, help_text="Comma-separated skill names, e.g. Python, SQL, Git", max_length=350)),
            ("published", models.BooleanField(default=True)),
            ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="courses.module")),
        ], options={"ordering": ["module__position", "position", "id"]}),
        migrations.AddConstraint(model_name="module",constraint=models.UniqueConstraint(fields=("course", "position"),name="unique_module_position_per_course")),
    ]
