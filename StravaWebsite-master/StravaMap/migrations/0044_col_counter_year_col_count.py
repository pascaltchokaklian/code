# Generated by Django 4.2 on 2023-11-18 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('StravaMap', '0043_user_var_last_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='col_counter',
            name='year_col_count',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]