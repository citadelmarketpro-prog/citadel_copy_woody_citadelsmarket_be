from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_expand_loyalty_tiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='can_transfer',
            field=models.BooleanField(
                default=False,
                help_text='Allow user to transfer funds between Balance and Profit accounts'
            ),
        ),
    ]
