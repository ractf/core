# Generated by Django 3.2.4 on 2021-07-19 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0017_merge_0016_auto_20210327_2315_0016_auto_20210408_1804'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='tiebreaker',
            field=models.BooleanField(default=True),
        ),
    ]