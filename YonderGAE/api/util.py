from db import YonderDb
import logging
from datetime import datetime

class Util(object):

	@staticmethod
	def email(subject, body, reply = ""):
		from google.appengine.api import mail
		sender_address = "yondervideos@gmail.com"
		user_address = "support@yonderfeed.com"
		# if reply != "":
		# 	mail.send_mail(sender_address, user_address, subject, body, reply_to = reply)
		# else:
		# 	mail.send_mail(sender_address, user_address, subject, body)