# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.utils import timezone
import pytz

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http.request import QueryDict
from django.shortcuts import render

from django.core.exceptions import NON_FIELD_ERRORS, ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from .models import User, Area, Keyword, Question, Reply, Vote, Notification
from .forms import UserForm, AreaForm, KeywordForm, QuestionForm, ReplyForm

from .tasks import send_email

PER_PAGE_NUM = 50
PER_PAGE_NUM_NOTIFICATOINS = 50
HOT_TRESHOLD = 3

# Create your views here.	
def parse(values):
	preds = values.split(',')
	cleaned_values = [pred.strip() for pred in preds if pred.strip() != '']
	return cleaned_values

def handle(request, field):
	data = request.POST.get(field,'').strip()
	if data == '':
		return None
	cleaned_data = parse(data)
	if len(cleaned_data) == 0:
		 return None
	return cleaned_data

def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError

@require_http_methods(["GET"])
def serveWelcomePage(request):
	if str(request.user) != "AnonymousUser":
		return HttpResponseRedirect('/profile/')
	return render( request, 'app/welcome.html' )

@require_http_methods(["GET"])
def serveSignUpPage(request):
	return render( request, 'app/sign_up_page.html' )

@require_http_methods(["GET"])
def serveSignInPage(request):
	return render( request, 'app/sign_in_page.html' )

@require_http_methods(["POST"])
def signUp(request):
	if request.method == 'POST':
		if request.POST.get('password','') != request.POST.get('password2',''):
			 return HttpResponse(json.dumps( {'password':['password_mismatch']} ), content_type="application/json")

		areas = handle(request, "areas")
		if areas == None:
			return HttpResponse(json.dumps( {"areas":['missing_areas']} ), content_type="application/json")

		user_areas = []
		for area in areas:
			q_dict = QueryDict()
			valid_form_object = q_dict.fromkeys(['area'], area)
			area_f = AreaForm( valid_form_object )
			if area_f.is_valid():
				try:
					existing_area = Area.objects.get(area=area_f.cleaned_data.get('area',''))
					user_areas.append(existing_area)
				except ObjectDoesNotExist:
					new_area = area_f.save()
					user_areas.append(new_area)
			else:
				return HttpResponse(json.dumps(area_f._errors), content_type="application/json")

		new_userf = UserForm(request.POST)

		if new_userf.is_valid():
			new_user = new_userf.save()
			for user_area in user_areas:
				new_user.areas.add(user_area)
			login(request, new_user)
			request.session.set_expiry(0)
			send_email.delay(new_user.username, new_user.verification_code, new_user.email)
			return HttpResponseRedirect('/serve_verification_page/')
		else:
			return HttpResponse(json.dumps(new_userf._errors), content_type="application/json")


@require_http_methods(["GET"])
@login_required(login_url='/')
def serveVerificationPage(request):
	return render( request, 'app/verification_page.html' )


@require_http_methods(["POST"])
@login_required(login_url='/')
def verifyCode(request):
	if request.method == 'POST':
		verification_code = request.POST.get('verification_code','')
		user = User.objects.get(pk=request.user.id)
		if verification_code == user.verification_code:
			user.is_verified = True;
			user.save()
			return HttpResponseRedirect('/profile/')
		else:
			return HttpResponse(json.dumps( {'verification':['verification code did not match']} ), content_type="application/json")


@require_http_methods(["POST"])
def signIn(request):
	if request.method == 'POST':
		username = request.POST.get('username','')
		password = request.POST.get('password','')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			if user.is_verified:
				login(request, user)
				return HttpResponseRedirect('/profile/')
			else:
				return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
		else:
			return HttpResponse(json.dumps( {'login':['invalid']} ), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def _logout(request):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	
	if request.method == 'GET':
		logout(request)
		return HttpResponseRedirect('/')


@require_http_methods(["GET"])
@login_required(login_url='/')
def serveProfilePage(request):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	user = User.objects.get(pk=request.user.id)
	context = {
		'username':user.username
	}
	return render( request, 'app/profile.html', context )


@require_http_methods(["POST"])
@login_required(login_url='/')
def ask(request):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	
	if request.method == 'POST':
		areas = handle(request, "areas")
		keywords = handle(request, "keywords")

		if areas == None:
			return HttpResponse(json.dumps( {"areas":['missing_areas']} ), content_type="application/json")
		if keywords == None:
			return HttpResponse(json.dumps( {"keywords":['missing_keywords']} ), content_type="application/json")

		question_areas = []
		question_keywords  = []

		for area in areas:
			q_dict = QueryDict()
			valid_form_object = q_dict.fromkeys(['area'], area)
			area_f = AreaForm( valid_form_object )
			if area_f.is_valid():
				try:
					existing_area = Area.objects.get(area=area_f.cleaned_data.get('area',''))
					question_areas.append(existing_area)
				except ObjectDoesNotExist:
					new_area = area_f.save()
					question_areas.append(new_area)
			else:
				return HttpResponse(json.dumps(area_f._errors), content_type="application/json")

		for keyword in keywords:
			q_dict = QueryDict()
			valid_form_object = q_dict.fromkeys(['keyword'], keyword)
			keyword_f = KeywordForm( valid_form_object )
			if keyword_f.is_valid():
				try:
					existing_keyword = Keyword.objects.get(keyword=keyword_f.cleaned_data.get('keyword',''))
					question_keywords.append(existing_keyword)
				except ObjectDoesNotExist:
					new_keyword = keyword_f.save()
					question_keywords.append(new_keyword)
			else:
				return HttpResponse(json.dumps(keyword_f._errors), content_type="application/json")

		new_questionf = QuestionForm(request.POST)

		if new_questionf.is_valid():
			new_question = new_questionf.save()

			for question_area in question_areas:
				new_question.areas.add(question_area)

			for question_keyword in question_keywords:
				new_question.keywords.add(question_keyword)

			new_question.user = request.user
			new_question.subscriber_count = 1 
			new_question.subscriptions.add(request.user)
			new_question.save()
			new_question.user.asked_question_count = new_question.user.asked_question_count + 1
			new_question.user.save()

			return HttpResponse(json.dumps( {'success':['submitted']} ), content_type="application/json")
		else:
			return HttpResponse(json.dumps(new_questionf._errors), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def questionSubscribe(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	
	if request.method == 'GET':

		try:
			question = Question.objects.select_related().get( pk=_id )
			if question.subscriptions.filter( pk=request.user.id ).exists():
				return HttpResponse(json.dumps( {'questionSubscribe':['already_subscribed']} ), content_type="application/json")
			question.subscriptions.add(request.user)
			return HttpResponse(json.dumps( {'questionSubscribe':['success']} ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'questionSubscribe':['object does not exists']} ), content_type="application/json")


@require_http_methods(["GET"])
@login_required(login_url='/')
def questionUnsubscribe(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	
	if request.method == 'GET':

		try:
			question = Question.objects.select_related().get( pk=_id )
			if question.subscriptions.filter( pk=request.user.id ).exists():
				question.subscriptions.remove(request.user)
				return HttpResponse(json.dumps( {'questionUnsubscribe':['success']} ), content_type="application/json")
			else:
				return HttpResponse(json.dumps( {'questionUnsubscribe':['never_subscribed']} ), content_type="application/json")


		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'questionUnsubscribe':['object does not exists']} ), content_type="application/json")





@require_http_methods(["POST"])
@login_required(login_url='/')
def reply(request):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	
	if request.method == 'POST':
		keywords = handle(request, "keywords")
		if keywords == None:
			return HttpResponse(json.dumps( {"keywords":['missing_keywords']} ), content_type="application/json")

		reply_keywords  = []
		for keyword in keywords:
			q_dict = QueryDict()
			valid_form_object = q_dict.fromkeys(['keyword'], keyword)
			keyword_f = KeywordForm( valid_form_object )
			if keyword_f.is_valid():
				try:
					existing_keyword = Keyword.objects.get(keyword=keyword_f.cleaned_data.get('keyword',''))
					reply_keywords.append(existing_keyword)
				except ObjectDoesNotExist:
					new_keyword = keyword_f.save()
					reply_keywords.append(new_keyword)
			else:
				return HttpResponse(json.dumps(keyword_f._errors), content_type="application/json")

		new_replyf = ReplyForm(request.POST)

		if new_replyf.is_valid():

			try:
				question = Question.objects.get(pk=new_replyf.cleaned_data.get('in_reply_to_id',''))
				new_reply = Reply.objects.create(
					user=request.user, 
					question=question, 
					in_reply_to_id=new_replyf.cleaned_data.get('in_reply_to_id',''),
					reply=new_replyf.cleaned_data.get('reply','') )

				for reply_keyword in reply_keywords:
					new_reply.keywords.add(reply_keyword)

				question.reply_count = question.reply_count + 1
				question.save()
				new_reply.user.reply_count = new_reply.user.reply_count + 1
				new_reply.user.save()

				return HttpResponse(json.dumps( {'success':['submitted']} ), content_type="application/json")
			except ObjectDoesNotExist:
				return HttpResponse(json.dumps( {'in_reply_to_id':['question does not exists']} ), content_type="application/json")
			except Exception as e:
				return HttpResponse(json.dumps( {'reply':[str(e)] } ), content_type="application/json")

		else:
			return HttpResponse(json.dumps(new_replyf._errors), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def getQuestions(request, page=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	
	if request.method == 'GET':
		user = request.user
		response = { 	
						'total_page_num':0,
						'current_page':0,
						'per_page_num':0,
						'objects':[]
												 }
		
		try:
			questions = user.question_set.select_related().all().order_by('-date_created')
			count = questions.count()
			paginator = Paginator(questions, PER_PAGE_NUM)
			
			try:
				questions_per_page = paginator.page(page)
			except PageNotAnInteger:
				page = 1
				questions_per_page = paginator.page(page)
			except EmptyPage:
				page = 1
				questions_per_page = paginator.page(page)
				
			response['total_page_num'] = paginator.num_pages
			response['current_page'] = int(page)
			if count == 0:
				response['per_page_num'] = 0
			else:
				response['per_page_num'] = questions_per_page.end_index() - questions_per_page.start_index() + 1

			for question in questions_per_page:
				
				q_object = {}

				q_object['pk'] = question.pk
				q_object['username'] = question.user.username
				q_object['date_created'] = question.date_created
				q_object['keywords'] = [ keyword.keyword for keyword in question.keywords.all() ]
				q_object['subject'] = question.subject
				q_object['rating'] = question.rating
				q_object['view'] = question.view
				q_object['reply_count'] = question.reply_count
				q_object['areas'] = [ area.area for area in question.areas.all() ]

				response['objects'].append(q_object)

			return HttpResponse(json.dumps( response, default = date_handler ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'getQuestions':['object does not exists']} ), content_type="application/json")


@require_http_methods(["GET"])
@login_required(login_url='/')
def getSubscriptions(request, page=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")
	
	if request.method == 'GET':
		user = request.user
		response = { 	
						'total_page_num':0,
						'current_page':0,
						'per_page_num':0,
						'objects':[]
												 }
		
		try:
			questions = user.subscribed_questions.select_related().all().order_by('-date_created')
			count = questions.count()

			paginator = Paginator(questions, PER_PAGE_NUM)
			
			try:
				questions_per_page = paginator.page(page)
			except PageNotAnInteger:
				page = 1
				questions_per_page = paginator.page(page)
			except EmptyPage:
				page = 1
				questions_per_page = paginator.page(page)
				
			response['total_page_num'] = paginator.num_pages
			response['current_page'] = int(page)
			if count == 0:
				response['per_page_num'] = 0	
			else:
				response['per_page_num'] = questions_per_page.end_index() - questions_per_page.start_index() + 1

			for question in questions_per_page:
				
				q_object = {}

				q_object['pk'] = question.pk
				q_object['username'] = question.user.username
				q_object['date_created'] = question.date_created
				q_object['keywords'] = [ keyword.keyword for keyword in question.keywords.all() ]
				q_object['subject'] = question.subject
				q_object['rating'] = question.rating
				q_object['view'] = question.view
				q_object['reply_count'] = question.reply_count
				q_object['areas'] = [ area.area for area in question.areas.all() ]

				response['objects'].append(q_object)

			return HttpResponse(json.dumps( response, default = date_handler ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'getSubscriptions':['object does not exists']} ), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def getReplies(request, page=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		user = request.user
		response = { 	
						'total_page_num':0,
						'current_page':0,
						'per_page_num':0,
						'objects':[]
												 }
		try:
			replies = user.reply_set.select_related().all().order_by('-date_created')
			count = replies.count() 

			paginator = Paginator(replies, PER_PAGE_NUM)
			
			try:
				replies_per_page = paginator.page(page)
			except PageNotAnInteger:
				page = 1
				replies_per_page = paginator.page(page)
			except EmptyPage:
				page = 1
				replies_per_page = paginator.page(page)

			response['total_page_num'] = paginator.num_pages
			response['current_page'] = int(page)
			if count == 0:
				response['per_page_num'] = 0
			else:	
				response['per_page_num'] = replies_per_page.end_index() - replies_per_page.start_index() + 1

			for reply in replies_per_page:

				r_object = {}

				r_object['pk'] = reply.pk
				r_object['username'] = reply.user.username
				r_object['date_created'] = reply.date_created
				r_object['keywords'] = [ keyword.keyword for keyword in reply.keywords.all() ]
				r_object['in_reply_to_id'] = reply.in_reply_to_id
				r_object['rating'] = reply.rating
				r_object['in_reply_to_subject'] = reply.question.subject
				r_object['reply'] = reply.reply

				response['objects'].append( r_object )

			return HttpResponse(json.dumps( response, default = date_handler ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'getReplies':['object does not exists']} ), content_type="application/json")



@require_http_methods(["GET"])
def getQuestionDetails(request, _id=1, page=1 ):
	if request.method == 'GET':
		response = { 	
						'total_page_num':0,
						'current_page':0,
						'per_page_num':0,
						'question_object':{},
						'reply_objects':[]
					}
		try:
			question = Question.objects.select_related().get(pk=_id)
			#what if _id not integer
			question.view = question.view + 1
			question.save()

			response['question_object'] = {
											'pk':question.pk,
											'username': question.user.username,
											'date_created':question.date_created,
											'last_edited':question.last_edited,
											'rating':question.rating,
											'view':question.view,
											'areas':[ area.area for area in question.areas.all() ],
											'subject':question.subject,
											'description':question.description,
											'keywords':[ keyword.keyword for keyword in question.keywords.all() ],
											'reply_count':question.reply_count,
											'feed_group':question.feed_group
										}


			replies = question.reply_set.select_related().all().order_by('date_created')
			count = replies.count()

			paginator = Paginator(replies, PER_PAGE_NUM)
			
			try:
				replies_per_page = paginator.page(page)
			except PageNotAnInteger:
				page = 1
				replies_per_page = paginator.page(page)
			except EmptyPage:
				page = 1
				replies_per_page = paginator.page(page)

			response['total_page_num'] = paginator.num_pages
			response['current_page'] = int(page)
			if count == 0:
				response['per_page_num'] = 0
			else:	
				response['per_page_num'] = replies_per_page.end_index() - replies_per_page.start_index() + 1


			for reply in replies_per_page:

				r_object = {}

				r_object['pk'] = reply.pk
				r_object['username'] = reply.user.username
				r_object['date_created'] = reply.date_created
				r_object['keywords'] = [ keyword.keyword for keyword in reply.keywords.all() ]
				r_object['in_reply_to_id'] = reply.in_reply_to_id
				r_object['rating'] = reply.rating
				r_object['in_reply_to_subject'] = reply.question.subject
				r_object['reply'] = reply.reply

				response['reply_objects'].append(r_object)

			return HttpResponse(json.dumps( response, default = date_handler ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'getQuestionDetails':['object does not exists']} ), content_type="application/json")

def saveVote(user, vote_object, vote_action, vote_id):
	new_vote = Vote( user=user, vote_object=vote_object, vote_action=vote_action, vote_id=vote_id )
	new_vote.save()

@require_http_methods(["GET"])
@login_required(login_url='/')
def questionVoteUp(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		if Vote.objects.filter( user=request.user, vote_object='Q', vote_id=_id ).exists():
			return HttpResponse(json.dumps( {'questionVoteUp':['already_voted']} ), content_type="application/json")
		try:
			question = Question.objects.select_related().get(pk=_id)
			question.rating = question.rating + 1
			if question.rating > HOT_TRESHOLD:
				question.feed_group = 'H'
			else:
				question.feed_group = 'C'
			question.user.rating = question.user.rating + 1
			question.user.save()
			question.save()
			saveVote( request.user, 'Q', 'U', _id )
			return HttpResponse(json.dumps( {'questionVoteUp':['success']} ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'questionVoteUp':['object does not exists']} ), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def questionVoteDown(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		if Vote.objects.filter( user=request.user, vote_object='Q', vote_id=_id ).exists():
			return HttpResponse(json.dumps( {'questionVoteDown':['already_voted']} ), content_type="application/json")
		try:
			question = Question.objects.select_related().get(pk=_id)
			question.rating = question.rating - 1
			if question.rating > HOT_TRESHOLD:
				question.feed_group = 'H'
			else:
				question.feed_group = 'C'
			question.user.rating = question.user.rating - 1
			question.user.save()
			question.save()
			saveVote( request.user, 'Q', 'D', _id )
			return HttpResponse(json.dumps( {'success':['OK']} ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'error':['object does not exists']} ), content_type="application/json")

@require_http_methods(["GET"])
@login_required(login_url='/')
def deleteQuestion(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'error':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':

		try:
			question = Question.objects.select_related().get(pk=_id)
			if request.user.username == question.user.username:
				question.delete()
				return HttpResponse(json.dumps( {'success':['OK']} ), content_type="application/json")
			else:
				return HttpResponse(json.dumps( {'error':['not_authorized']} ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'error':['not_found']} ), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def deleteReply(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'error':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':

		try:
			reply = Reply.objects.select_related().get(pk=_id)
			if request.user.username == reply.user.username:
				reply.delete()
				return HttpResponse(json.dumps( {'success':['OK']} ), content_type="application/json")
			else:
				return HttpResponse(json.dumps( {'error':['not_authorized']} ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'error':['not_found']} ), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def replyVoteUp(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		if Vote.objects.filter( user=request.user, vote_object='R', vote_id=_id ).exists():
			return HttpResponse(json.dumps( {'replyVoteUp':['already_voted']} ), content_type="application/json")
		try:
			reply = Reply.objects.select_related().get(pk=_id)
			reply.rating = reply.rating + 1
			reply.user.rating = reply.user.rating + 1
			reply.user.save()
			reply.save()
			saveVote( request.user, 'R', 'U', _id )
			return HttpResponse(json.dumps( {'replyVoteUp':['success']} ), content_type="application/json")


		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'replyVoteUp':['object does not exists']} ), content_type="application/json")


@require_http_methods(["GET"])
@login_required(login_url='/')
def replyVoteDown(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		if Vote.objects.filter( user=request.user, vote_object='Q', vote_id=_id ).exists():
			return HttpResponse(json.dumps( {'replyVoteDown':['already_voted']} ), content_type="application/json")
		try:
			reply = Reply.objects.select_related().get(pk=_id)
			reply.rating = reply.rating - 1
			reply.user.rating = reply.user.rating - 1
			reply.user.save()
			reply.save()
			saveVote( request.user, 'R', 'D', _id )
			return HttpResponse(json.dumps( {'replyVoteDown':['success']} ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'replyVoteDown':['object does not exists']} ), content_type="application/json")



@require_http_methods(["GET"])
@login_required(login_url='/')
def getNotifications(request, page=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		user = request.user
		response = { 	
						'total_page_num':0,
						'current_page':0,
						'per_page_num':0,
						'objects':[]
												 }

		try:
			notifications = Notification.objects.select_related().filter( user=user, is_seen=False ).order_by('-date_created')
			count = notifications.count()

			if count == 0:
				return HttpResponse(json.dumps( {'getNotifications':['no_new_notifications']} ), content_type="application/json")

			paginator = Paginator(notifications, PER_PAGE_NUM_NOTIFICATOINS)

			try:
				notifications_per_page = paginator.page(page)
			except PageNotAnInteger:
				page = 1
				notifications_per_page = paginator.page(page)
			except EmptyPage:
				page = 1
				notifications_per_page = paginator.page(page)

			response['total_page_num'] = paginator.num_pages
			response['current_page'] = int(page)
			if count == 0:
				response['per_page_num'] = 0
			else:	
				response['per_page_num'] = notifications_per_page.end_index() - notifications_per_page.start_index() + 1

			for notification in notifications_per_page:

				n_object = {}

				n_object['pk'] = notification.pk
				n_object['date_created'] = notification.date_created
				n_object['is_seen'] = notification.is_seen
				n_object['notification_type'] = notification.notification_type
				n_object['source_id'] = notification.source_id
				n_object['message'] = notification.message

				response['objects'].append( n_object )

			return HttpResponse(json.dumps( response, default = date_handler ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'getNotifications':['object does not exists']} ), content_type="application/json")


@require_http_methods(["GET"])
@login_required(login_url='/')
def notify(request):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		user = request.user
		try:
			count = Notification.objects.select_related().filter( user=user, is_seen=False ).count()
			return HttpResponse(json.dumps( {'success':[count]} ), content_type="application/json")

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'error':['object does not exists']} ), content_type="application/json")

		except Exception as e:
			return HttpResponse(json.dumps( {'error':[str(e)]} ), content_type="application/json")


@require_http_methods(["GET"])
@login_required(login_url='/')
def viewNotification(request, _id=1):
	if request.user.is_verified == False:
		return HttpResponse(json.dumps( {'verification':['verification_required']} ), content_type="application/json")

	if request.method == 'GET':
		try:
			rel_link='/profile/'
			notification = Notification.objects.select_related().get(pk=_id)
			notification.is_seen = True
			notification.save()
			notification_type = notification.notification_type
			if notification_type == 'RE': # REPLY
				rel_link = '/questions/{0}/1'.format( notification.source_id )
			return HttpResponseRedirect(rel_link)

		except ObjectDoesNotExist:
			return HttpResponse(json.dumps( {'error':['object does not exists']} ), content_type="application/json")

		except Exception as e:
			return HttpResponse(json.dumps( {'error':[str(e)]} ), content_type="application/json")
