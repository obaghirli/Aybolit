# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-17 20:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_vote'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='subscriptions',
            field=models.ManyToManyField(blank=True, default=None, related_name='subscribed_users', to=settings.AUTH_USER_MODEL),
        ),
    ]
