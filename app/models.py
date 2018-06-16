# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
import pytz

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class Area(models.Model):
	area = models.CharField(max_length = 200, null = False, blank = False) 

class Keyword(models.Model):
	keyword = models.CharField(max_length = 200, null = False, blank = False)

class Vote(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, null = True, blank = True, default = None )
	vote_object = models.CharField(max_length=1, null = True, blank = True) #R-REPLY, Q-QUESTION
	vote_action = models.CharField(max_length=1, null = True, blank = True) #U-UP, D-DOWN
	vote_id = models.PositiveIntegerField(null = True, blank = True)


class User(AbstractUser):
	username = models.CharField(max_length = 150, null = False, blank = False, unique=True)
	password = models.CharField(max_length = 300, null = False, blank = False)
	email = models.CharField(max_length = 150, null = False, blank = False)

	is_doc = models.BooleanField(default = False, blank = True)
	organisation = models.CharField(default = '', max_length = 300, null = False, blank = True)
	areas = models.ManyToManyField(Area, blank=True, default=None)
	rating = models.PositiveIntegerField(default = 0, null = False, blank = True)

	asked_question_count = models.PositiveIntegerField(default = 0, null = False, blank = True)
	reply_count = models.PositiveIntegerField(default = 0, null = False, blank = True)
	is_verified = models.BooleanField(default = False, blank = True)
	verification_code = models.CharField(max_length=6, null = False, blank = True)

class Question(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, null = True, blank = True, default = None )
	subscriptions = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, default=None, related_name='subscribed_questions')
	date_created = models.DateTimeField(default=timezone.now, null = False, blank = True)
	last_edited = models.DateTimeField(default=timezone.now, null = False, blank = True)
	rating = models.PositiveIntegerField(default = 0, null = False, blank = True)

	view = models.PositiveIntegerField(default = 0, null = False, blank = True)

	areas = models.ManyToManyField(Area, blank=True, default=None)
	subject = models.CharField(max_length = 200, null = False, blank = False)
	description = models.CharField(max_length = 1000, null = False, blank = False)
	keywords = models.ManyToManyField(Keyword, blank=True, default=None)

	reply_count = models.PositiveIntegerField(default = 0, null = False, blank = True)
	feed_group = models.CharField(default = 'C', max_length=1, null = False, blank = True) #[hot, cold ] /H C N



class Reply(models.Model):
 	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, null = True, blank = True, default = None )
 	question = models.ForeignKey(Question, on_delete = models.CASCADE, null = True, blank = True, default = None )

 	date_created = models.DateTimeField(default=timezone.now, null = False, blank = True)
 	last_edited = models.DateTimeField(default=timezone.now, null = False, blank = True)
 	rating = models.PositiveIntegerField(default = 0, null = False, blank = True)

 	in_reply_to_id = models.PositiveIntegerField(null = False, blank = False)
 	reply = models.CharField(max_length = 1000, null = False, blank = False)
 	keywords = models.ManyToManyField(Keyword, blank=True, default=None)



class Notification(models.Model):
	 user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, null = True, blank = True, default = None )
	 date_created = models.DateTimeField(default=timezone.now, null = False, blank = True)
	 message = models.CharField(max_length = 300, null = False, blank = False)
	 is_seen = models.BooleanField(default = False, blank = True)
	 notification_type = models.CharField(max_length=2, null = True, blank = True) #RE - reply
	 source_id = models.PositiveIntegerField(null = True, blank = True)


@receiver(post_save, sender=Reply)
def save_notification_reply(sender, **kwargs):
	if kwargs.get('created', False):
		reply = kwargs.get('instance', None)
		question = reply.question
		subscriptions = question.subscriptions.all()

		for subscription in subscriptions:
			if subscription.username == reply.user.username:
				continue

			if not Notification.objects.filter( user=subscription, source_id=reply.in_reply_to_id, is_seen=False ).exists():
				Notification.objects.create(
						user = subscription,
						notification_type = 'RE',
						source_id = reply.in_reply_to_id,
						message = question.subject
					)

