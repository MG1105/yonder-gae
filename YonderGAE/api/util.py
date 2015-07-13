from db import YonderDb
import logging
from datetime import datetime

class User(object):

	def verify(self, user_id):
		yonderdb = YonderDb()
		user_info = yonderdb.get_user_info(user_id)

		if user_info["warn"] is None:
			user_info["warn"] = 0
		elif user_info["warn"] == 1:
			yonderdb.user_warned(user_id)
		else:
			user_info["warn"] = 0

		if user_info["ban"] is None:
			user_info["ban"] = 0
		elif user_info["ban"] > datetime.utcnow():
			user_info["ban"] = 1
		else:
			user_info["ban"] = 0

		return user_info