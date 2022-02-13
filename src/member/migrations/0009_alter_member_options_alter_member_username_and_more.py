# Generated by Django 4.0.2 on 2022-02-11 21:43

import backend.validators
from django.db import migrations, models
import django.db.models.functions.text


def truncate_usernames(apps, schema_editor):
    Member = apps.get_model('member', 'member')
    db_alias = schema_editor.connection.alias
    for member in Member.objects.using(db_alias).all():
        if len(member.username) > 36:
            member.username = member.username[:36]
            member.save()


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0008_remove_member_password_reset_token'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='member',
            options={},
        ),
        migrations.RunPython(
            truncate_usernames,
            # Marked as elidable since when we squash we will have the 36 characters
            # in by default
            elidable=True,
        ),
        migrations.AlterField(
            model_name='member',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 36 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=36, unique=True, validators=[backend.validators.printable_name], verbose_name='username'),
        ),
        migrations.AddConstraint(
            model_name='member',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('username'), name='member_member_username_uniq_idx'),
        ),
    ]
