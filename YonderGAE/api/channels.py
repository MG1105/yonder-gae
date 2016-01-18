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
