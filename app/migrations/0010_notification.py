# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-22 20:57
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20171218_0112'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('message', models.CharField(max_length=300)),
                ('is_seen', models.BooleanField(default=False)),
                ('notification_type', models.CharField(blank=True, max_length=2, null=True)),
                ('source_id', models.PositiveIntegerField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
