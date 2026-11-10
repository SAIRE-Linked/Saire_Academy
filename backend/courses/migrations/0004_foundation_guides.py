from django.db import migrations
from courses.foundations_v104 import add_foundation_guides


def seed(apps, schema_editor):
    add_foundation_guides(apps, schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [('courses', '0003_glossaryentry_formativequestion_learningresource_and_more')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
