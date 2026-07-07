from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0028_alter_customuser_target_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="news",
            name="external_image_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="news",
            name="source_url",
            field=models.URLField(blank=True, default=""),
        ),
    ]
