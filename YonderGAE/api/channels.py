import cloudstorage as gcs
import logging
import math
from db import YonderDb
from random import randint

class Channels(object):

	def get_channels(self, user_id, sort):
		yonderdb = YonderDb()
		channels = yonderdb.get_channels(user_id, sort)
		return channels

	def add_channel(self, channel, user_id, nsfw):
		yonderdb = YonderDb()
		yonderdb.add_channel(channel, user_id, nsfw)

	def rate_channel(self, channel_id, rating, user_id):
		yonderdb = YonderDb()
		yonderdb.rate_channel(channel_id, rating, user_id)
