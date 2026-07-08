from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0030_alter_news_external_image_url_alter_news_source_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='category',
            field=models.CharField(
                choices=[
                    ('stock',   'Stock'),
                    ('crypto',  'Crypto'),
                    ('etf',     'ETF'),
                    ('indices', 'Indices'),
                    ('forex',   'Forex'),
                ],
                default='stock',
                max_length=20,
            ),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['category'], name='app_stock_category_idx'),
        ),
    ]
