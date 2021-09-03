# Generated by Django 3.0.5 on 2020-08-08 13:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hint', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenges', '0002_auto_20200808_1337'),
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hintuse',
            name='teams',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hints_used', to='team.Team'),
        ),
        migrations.AddField(
            model_name='hintuse',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hints_used', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='hint',
            name='challenges',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hint_set', to='challenge.Challenge'),
        ),
        migrations.AlterUniqueTogether(
            name='hintuse',
            unique_together={('hint', 'teams')},
        ),
    ]
