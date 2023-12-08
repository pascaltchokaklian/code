# Generated by Django 4.2 on 2023-11-04 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('StravaMap', '0029_remove_user_var_view_region_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Month',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strava_user_id', models.IntegerField(null=True)),
                ('yearmonth', models.CharField(default='190000', max_length=6)),
                ('days_on', models.IntegerField(null=True)),
                ('bike_km', models.IntegerField(null=True)),
                ('bike_ascent', models.IntegerField(null=True)),
                ('col_count', models.IntegerField(null=True)),
                ('col2000_count', models.IntegerField(null=True)),
            ],
        ),
    ]