# Generated by Django 5.1.6 on 2025-02-20 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0009_alter_subjectmapping_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='course',
            name='duration_in_months',
            field=models.CharField(default=24, max_length=15),
        ),
        migrations.AddField(
            model_name='course',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='department',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='designation',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='salutation',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='specialization',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='terms',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
