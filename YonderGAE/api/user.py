import cloudstorage as gcs
import logging
import math
from db import YonderDb
from random import randint

class User(object):

	def get_profile(self, profile_id, user_id):
		yonderdb = YonderDb()
		profile = yonderdb.get_profile(profile_id, user_id)
		return profile

	def add_profile(self, android_id, account_id, first_name, last_name, email, username, college):
		yonderdb = YonderDb()
		yonderdb.add_profile(android_id, account_id, first_name, last_name, email, username, college)

	def setFollow(self, user_id, following, follow):
		yonderdb = YonderDb()
		if follow == "1":
			yonderdb.follow(user_id, following)
		else:
			yonderdb.unfollow(user_id, following)

	def giveGold(self, user_id, following, video_id):
		yonderdb = YonderDb()
		return yonderdb.giveGold(user_id, following, video_id)

	def verify(self, user_id, version):
		yonderdb = YonderDb()
		yonderdb.update_last_request(user_id, version)

		if int(version) < 10:
			upgrade = 2
		else:
			upgrade = 0
		user_info = yonderdb.get_user_info(user_id, upgrade)

		# warn is null = never warned, send 0
		# warn is 1 sends 1 aka warning and set to 0
		# warn 0 send -1 to tell client already warned
		if user_info["warn"] is None:
			user_info["warn"] = 0
		elif user_info["warn"] == 1:
			yonderdb.user_warned(user_id)
		else:
			user_info["warn"] = -1

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

	def unlock(self, user_id, code):
		yonderdb = YonderDb()
		return yonderdb.unlock(user_id, code)

	def invited(self, user_id, invited_by):
		yonderdb = YonderDb()
		yonderdb.invited(user_id, invited_by)

	def join_waitlist(self, user_id, email):
		yonderdb = YonderDb()
		yonderdb.join_waitlist(user_id, email)



