# Generated by Django 5.1.6 on 2025-04-22 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0035_remove_resetexamrequest_specialization'),
    ]

    operations = [
        migrations.AddField(
            model_name='hallticketannounce',
            name='type',
            field=models.CharField(choices=[('main', 'main'), ('resit-1', 'resit-1'), ('resit-2', 'resit-2')], default='main', max_length=150),
        ),
    ]
