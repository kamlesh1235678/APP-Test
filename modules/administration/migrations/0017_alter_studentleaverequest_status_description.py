# Generated by Django 5.1.6 on 2025-03-06 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0016_studentleaverequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentleaverequest',
            name='status_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
