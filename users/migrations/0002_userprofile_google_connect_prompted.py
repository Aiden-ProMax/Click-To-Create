from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='google_connect_prompted',
            field=models.BooleanField(default=False),
        ),
    ]
