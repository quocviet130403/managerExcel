# Generated by Django 4.2.2 on 2023-06-28 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FormData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20)),
                ('street_address', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('organization_name', models.CharField(max_length=100)),
                ('website', models.URLField(blank=True)),
                ('instagram', models.URLField(blank=True)),
                ('facebook', models.URLField(blank=True)),
                ('ticktock', models.URLField(blank=True)),
                ('twitter', models.URLField(blank=True)),
                ('youtube', models.URLField(blank=True)),
                ('description', models.TextField()),
                ('notes', models.TextField()),
                ('is_church', models.BooleanField(default=False)),
                ('is_organization', models.BooleanField(default=False)),
                ('is_influencer', models.BooleanField(default=False)),
                ('is_media', models.BooleanField(default=False)),
                ('services', models.CharField(max_length=100)),
                ('has_supported_movie_screenings', models.BooleanField(default=False)),
                ('has_supported_meetings', models.BooleanField(default=False)),
                ('has_supported_events', models.BooleanField(default=False)),
            ],
        ),
    ]