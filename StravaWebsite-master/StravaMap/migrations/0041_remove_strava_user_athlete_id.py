# Generated by Django 4.2 on 2023-11-13 07:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('StravaMap', '0040_remove_user_var_strava_user_user_var_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='strava_user',
            name='athlete_id',
        ),
    ]