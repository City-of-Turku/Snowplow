# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-29 06:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0003_add_last_location_to_vehicle'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vehicle',
            name='location_is_latest',
        ),
    ]
