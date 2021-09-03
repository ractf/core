# Generated by Django 3.0.5 on 2020-08-08 20:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenges', '0004_challenge_post_score_explanation'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChallengeFeedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback', models.TextField()),
                ('challenges', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Challenge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
