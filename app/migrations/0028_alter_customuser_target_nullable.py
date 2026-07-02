from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0027_trader_profit_share'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='target',
            field=models.DecimalField(
                verbose_name='Deposit Target',
                max_digits=20,
                decimal_places=2,
                default=50000.00,
                null=True,
                help_text='Admin-set deposit target shown as a progress bar on the user\'s portfolio page.',
            ),
        ),
    ]
