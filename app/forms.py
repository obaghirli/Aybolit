# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
import random

from django.utils.translation import ugettext as _
from django.forms import ModelForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError, ObjectDoesNotExist
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password

from .models import User, Area, Keyword, Question, Reply


random.seed(datetime.now())

class UserForm(ModelForm):
	class Meta:
		model = User
		fields = [
					'username',
					'password',
					'email',

					'is_doc',
					'organisation',
					'rating',

					'asked_question_count',
					'reply_count',
					'is_verified',
					'verification_code'
				]


	def clean_username(self):
		if not self.cleaned_data.get('username','').isalnum():
			raise ValidationError(_('username can only be alphanumeric'), code='username')

		if User.objects.filter(username=self.cleaned_data.get('username','')).exists():
			raise ValidationError(_('username_exists'), code='username')
		return self.cleaned_data.get('username','')

	def clean_password(self):
		for c in [ ' ', "'",'"','<','>','?','/','\n' ,'(','[','{']:
			if c in self.cleaned_data.get('password',''):
				raise ValidationError(_('illegal character'), code='password')
		validate_password( self.cleaned_data.get('password','') )
		hashed_password = make_password( self.cleaned_data.get('password','') )
		return hashed_password

	def clean_email(self):
		validate_email( self.cleaned_data.get('email','') )
		if User.objects.filter(email=self.cleaned_data.get('email','')).exists():
			raise ValidationError(_('email_exists'), code='email')
		return self.cleaned_data.get('email','')

	def clean_is_doc(self):
		if not isinstance( self.cleaned_data.get('is_doc',''), bool) :
			raise ValidationError(_('not_boolean'), code='is_doc')
		return self.cleaned_data.get('is_doc','')

	def clean_organisation(self):
		return self.cleaned_data.get('organisation','')

	def clean_is_verified(self):
		return False

	def clean_verification_code(self):
		return str(random.randint(100000,999999))

	# def clean(self):
	# 	cleaned_data = super( UserForm, self ).clean()
	# 	is_doc = cleaned_data.get('is_doc','')
	# 	preferences = cleaned_data.get('preferences','')
	# 	if is_doc == True and preferences == '':
	# 		raise ValidationError(_('missing_preferences'), code='preferences')

class AreaForm(ModelForm):
	class Meta:
		model = Area
		fields = [
					'area',
				]

	def clean_area(self):
		area =  self.cleaned_data.get('area','')
		if area == '':
			raise ValidationError(_('improper_area'), code='area')
		if not area.isalpha():
			raise ValidationError(_('improper_area'), code='area')
		return self.cleaned_data.get('area','')

class KeywordForm(ModelForm):
	class Meta:
		model = Keyword
		fields = [
					'keyword',
				]

	def clean_keyword(self):
		keyword =  self.cleaned_data.get('keyword','')
		if keyword == '':
			raise ValidationError(_('improper_keyword'), code='keyword')

		return self.cleaned_data.get('keyword','')


class QuestionForm(ModelForm):
	class Meta:
		model = Question
		fields = [
					'user',
					'date_created',
					'last_edited',
					'rating',
					'view',

					'subject',
					'description',

					'reply_count',
					'feed_group'
				]


	def clean_subject(self):
		subject = self.cleaned_data.get('subject','')
		if len(subject) == 0:
			raise ValidationError(_('can not be empty'), code='subject')
		return self.cleaned_data.get('subject','')

	def clean_description(self):
		description = self.cleaned_data.get('description','')
		description = description.strip()
		if len(description) == 0:
			raise ValidationError(_('can not be empty'), code='description')
		return self.cleaned_data.get('description','')



class ReplyForm(ModelForm):
	class Meta:
		model = Reply
		fields = [
					'user',
					'question',

					'date_created',
					'last_edited',
					'rating',

					'in_reply_to_id',
					'reply'

				]


	def clean_reply(self):
		reply = self.cleaned_data.get('reply','')
		reply = reply.strip()
		if len(reply) == 0:
			raise ValidationError(_('can not be empty'), code='reply')
		return self.cleaned_data.get('reply','')
