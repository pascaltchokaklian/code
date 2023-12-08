# Generated by Django 4.2 on 2023-05-31 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('StravaMap', '0003_activity_act_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activity',
            old_name='act_begin_date',
            new_name='act_start_date',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='act_avg',
        ),
        migrations.AddField(
            model_name='activity',
            name='strava_id',
            field=models.IntegerField(default=0),
        ),
    ]