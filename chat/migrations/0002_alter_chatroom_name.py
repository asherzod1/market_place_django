# Generated by Django 5.0 on 2024-04-30 12:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatroom",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
