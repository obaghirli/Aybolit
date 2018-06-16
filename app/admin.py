# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Area, Keyword, Question, Reply, Vote, Notification
# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Area)
admin.site.register(Keyword)
admin.site.register(Question)
admin.site.register(Reply)
admin.site.register(Vote)
admin.site.register(Notification)
