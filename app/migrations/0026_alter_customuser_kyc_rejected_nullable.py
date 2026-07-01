from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0025_customuser_kyc_rejected'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='kyc_rejected',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
