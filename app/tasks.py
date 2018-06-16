# Create your tasks here
from __future__ import absolute_import, unicode_literals

from smtplib import SMTPAuthenticationError

from django.core.mail import send_mail

from celery import shared_task

from .models import User, Area, Keyword, Question, Reply, Vote


@shared_task
def send_email(username, verification_code, email):
	subject = 'Aibolit'
	message = 'Thank you for registering at Aibolit.io.\n\nUsername: {0}\nVerification code: {1}\n\n\nBest Regards,\nAibolit'.format(username, verification_code)
	from_email = 'aybolito.noreply@gmail.com'
	recipient_list = [email]
	try:
		send_mail( subject, message, from_email, recipient_list, fail_silently = False )
		return 'success'
	except SMTPAuthenticationError:
		return 'failure: send email failed: to: {0}'.format(email)
