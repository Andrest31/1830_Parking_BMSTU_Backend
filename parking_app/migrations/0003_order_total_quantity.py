# Generated by Django 5.2 on 2025-04-11 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parking_app', '0002_alter_parking_description_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='total_quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
