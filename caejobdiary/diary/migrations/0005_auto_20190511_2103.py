# Generated by Django 2.0.9 on 2019-05-11 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0004_job_keywords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keyword',
            name='word',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]