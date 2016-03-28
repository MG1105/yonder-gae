import cloudstorage as gcs
import logging
import math
from db import YonderDb
from random import randint

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

class Upload(object):

	def add_video(self, video, caption, user_id, channel):
		file_name = "/yander/" + video.filename
		logging.info("Adding new video %s" % video.filename[:-4])
		logging.debug("Caption '%s' User %s Channel %s" % (caption, user_id, channel))
		write_retry_params = gcs.RetryParams(backoff_factor=1.1)
		gcs_file = gcs.open(file_name,
		                    "w",
		                    content_type="video/mp4",
		                    options={"x-goog-acl": "public-read"},
		                    retry_params=write_retry_params)
		file_content = video.file.read()
		gcs_file.write(file_content)
		gcs_file.close()
		yonderdb = YonderDb()
		yonderdb.add_video(video.filename[:-4], caption, user_id, channel)


class Feed(object):

	def get_videos(self, user_id, channel, channel_sort):
		yonderdb = YonderDb()
		video_ids = yonderdb.get_videos(user_id, channel, channel_sort)
		videos_info = []
		if len(video_ids) > 0:
			videos_info = yonderdb.get_video_info(video_ids, user_id)
		yonderdb.add_seen(user_id, video_ids)
		return videos_info

	def get_video(self, user_id, video):
		yonderdb = YonderDb()
		video_ids = [video]
		videos_info = yonderdb.get_video_info(video_ids, user_id)
		return videos_info

	def get_videos_info(self, video_ids):
		yonderdb = YonderDb()
		videos_info = []
		if len(video_ids) > 0:
			videos_info = yonderdb.get_video_info(video_ids, user_id)
		return videos_info


class Video(object):
	def add_rating(self, video_id, rating, user_id):
		yonderdb = YonderDb()
		yonderdb.rate_video(video_id, int(rating), user_id)
