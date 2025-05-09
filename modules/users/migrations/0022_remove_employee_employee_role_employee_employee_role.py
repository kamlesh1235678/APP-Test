# Generated by Django 5.1.6 on 2025-04-11 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0030_attendance_ce_marks'),
        ('users', '0021_alter_employee_designation_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='employee_role',
        ),
        migrations.AddField(
            model_name='employee',
            name='employee_role',
            field=models.ManyToManyField(related_name='employees_roles', to='administration.role'),
        ),
    ]
