# Generated by Django 4.2 on 2023-05-31 04:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('StravaMap', '0002_activity_col_counter_col_perform'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='act_name',
            field=models.CharField(default='', max_length=200, null=True),
        ),
    ]
