# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-13 21:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20171213_2201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='feed_group',
            field=models.CharField(blank=True, default='C', max_length=1),
        ),
    ]
