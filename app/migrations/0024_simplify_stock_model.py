import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_add_target_to_user'),
    ]

    operations = [
        # Remove price-related and metadata fields
        migrations.RemoveField(model_name='stock', name='logo_url'),
        migrations.RemoveField(model_name='stock', name='price'),
        migrations.RemoveField(model_name='stock', name='change'),
        migrations.RemoveField(model_name='stock', name='change_percent'),
        migrations.RemoveField(model_name='stock', name='volume'),
        migrations.RemoveField(model_name='stock', name='market_cap'),
        migrations.RemoveField(model_name='stock', name='sector'),
        # Change symbol to free-text (no choices, wider max_length)
        migrations.AlterField(
            model_name='stock',
            name='symbol',
            field=models.CharField(max_length=20, unique=True),
        ),
        # Add Cloudinary image field
        migrations.AddField(
            model_name='stock',
            name='image',
            field=cloudinary.models.CloudinaryField(
                blank=True, max_length=255, null=True,
                verbose_name='image', folder='stock_images',
            ),
        ),
    ]
