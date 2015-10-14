from db import YonderDb
import logging
from datetime import datetime

class User(object):

	def verify(self, user_id, version):
		yonderdb = YonderDb()
		yonderdb.update_last_request(user_id)

		if version == "1":
			upgrade = 0
		else:
			upgrade = 0
		user_info = yonderdb.get_user_info(user_id, upgrade)

		if user_info["warn"] is None:
			user_info["warn"] = 0
		elif user_info["warn"] == 1:
			yonderdb.user_warned(user_id)
		else:
			user_info["warn"] = 0

		# 1 for a week, 2 for a month
		if user_info["ban"] is None:
			user_info["ban"] = 0
		elif user_info["ban"] > datetime.utcnow():
			user_info["ban"] = 1
		else:
			user_info["ban"] = 0

		return user_info

	def get_score(self, user_id):
		yonderdb = YonderDb()
		return yonderdb.get_score(user_id)

	def ping(self, user_id):
		yonderdb = YonderDb()
		yonderdb.update_last_ping(user_id)

	@staticmethod
	def email(subject, body):
		from google.appengine.api import mail
		sender_address = "yondervideos@gmail.com"
		user_address = "support@yonderfeed.com"
		mail.send_mail(sender_address, user_address, subject, body)