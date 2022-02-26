# Generated by Django 4.0.2 on 2022-02-26 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0021_challenge_maintenance'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='current_score',
            field=models.IntegerField(help_text='The dynamically updated score for this challenge, null if the challenge is statically scored.', null=True),
        ),
    ]