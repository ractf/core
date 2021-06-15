# Generated by Django 3.2.4 on 2021-06-15 17:26

from django.db import migrations, models

import authentication.logic.utils


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0009_auto_20200831_2020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backupcode',
            name='code',
            field=models.CharField(default=authentication.logic.utils.random_backup_code, max_length=8),
        ),
        migrations.AlterField(
            model_name='passwordresettoken',
            name='expires',
            field=models.DateTimeField(default=authentication.logic.utils.one_day_hence),
        ),
    ]
