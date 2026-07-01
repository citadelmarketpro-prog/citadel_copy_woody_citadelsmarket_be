from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_simplify_stock_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='kyc_rejected',
            field=models.BooleanField(default=False),
        ),
    ]
