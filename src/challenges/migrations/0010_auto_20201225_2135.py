# Generated by Django 3.1 on 2020-12-25 21:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0009_file_md5'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challengevote',
            name='challenges',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='challenge.challenge'),
        ),
    ]
