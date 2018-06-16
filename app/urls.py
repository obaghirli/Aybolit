from django.conf.urls import url, include 
from . import views

urlpatterns = [
	url(r'^$', views.serveWelcomePage, name='serveWelcomePage'),
	url(r'^serve_sign_up_page/$', views.serveSignUpPage, name='serveSignUpPage'),
	url(r'^serve_sign_in_page/$', views.serveSignInPage, name='serveSignInPage'),

	url(r'^signup/$', views.signUp, name='signUp'),
	url(r'^serve_verification_page/$', views.serveVerificationPage, name='serveVerificationPage'),
	url(r'^verify/$', views.verifyCode, name='verifyCode'),

	url(r'^signin/$', views.signIn, name='signIn'),

	url(r'^questions/(?P<_id>\d+)/(?P<page>\d+)/$', views.getQuestionDetails, name='getQuestionDetails'),
	
	url(r'^profile/$', views.serveProfilePage, name='serveProfilePage'),
	url(r'^profile/ask$', views.ask, name='ask'),
	url(r'^profile/reply$', views.reply, name='reply'),
	url(r'^profile/getquestions/(?P<page>\d+)/$', views.getQuestions, name='getQuestions'),
	url(r'^profile/getreplies/(?P<page>\d+)/$', views.getReplies, name='getReplies'),
	url(r'^profile/getsubscriptions/(?P<page>\d+)/$', views.getSubscriptions, name='getSubscriptions'),

	url(r'^profile/questions/voteup/(?P<_id>\d+)/$', views.questionVoteUp, name='questionVoteUp'),
	url(r'^profile/questions/votedown/(?P<_id>\d+)/$', views.questionVoteDown, name='questionVoteDown'),
	url(r'^profile/questions/subscribe/(?P<_id>\d+)/$', views.questionSubscribe, name='questionSubscribe'),
	url(r'^profile/questions/unsubscribe/(?P<_id>\d+)/$', views.questionUnsubscribe, name='questionUnsubscribe'),
	url(r'^profile/questions/delete/(?P<_id>\d+)/$', views.deleteQuestion, name='deleteQuestion'),

	url(r'^profile/replies/voteup/(?P<_id>\d+)/$', views.replyVoteUp, name='replyVoteUp'),
	url(r'^profile/replies/votedown/(?P<_id>\d+)/$', views.replyVoteDown, name='replyVoteDown'),
	url(r'^profile/replies/delete/(?P<_id>\d+)/$', views.deleteReply, name='deleteReply'),

	url(r'^profile/notifications/(?P<page>\d+)/$', views.getNotifications, name='getNotifications'),
	url(r'^profile/notifications/notify/$', views.notify, name='notify'),
	url(r'^profile/notifications/view/(?P<_id>\d+)/$', views.viewNotification, name='viewNotification'),


	url(r'^profile/logout/$', views._logout, name='_logout')

]
