import os
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('footprint_service', '0001_initial'),
    ]

    def generate_superuser(apps, schema_editor):
        from django.contrib.auth.models import User

        superuser = User.objects.create_superuser(
            username=os.environ.get('DJANGO_SUPERUSER_NAME'),
            email=os.environ.get('DJANGO_SUPERUSER_EMAIL'),
            password=os.environ.get('DJANGO_SUPERUSER_PASSWORD'))

        superuser.save()

    operations = [
        migrations.RunPython(generate_superuser),
    ]
