# Generated by Django 5.0.4 on 2024-05-05 20:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="description",
            field=models.TextField(null=True),
        ),
    ]
