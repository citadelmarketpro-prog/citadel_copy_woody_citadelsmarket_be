from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_add_user_investment_to_copy_trade_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='usertradercopy',
            name='cancel_requested',
            field=models.BooleanField(
                default=False,
                help_text='User has requested to stop copying this trader'
            ),
        ),
        migrations.AddField(
            model_name='usertradercopy',
            name='cancel_requested_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When the cancel request was submitted'
            ),
        ),
    ]
