# Generated by Django 5.0 on 2024-02-07 10:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("announcement", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="transports",
            name="ri",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
