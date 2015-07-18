import cloudstorage as gcs
import logging
import math
from db import YonderDb

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

class Upload(object):

	def add_video(self, video, caption, user_id, longitude, latitude):
		file_name = "/yander/" + video.filename
		logging.info("Adding new video %s" % video.filename[:-4])
		logging.debug("Caption '%s' User %s Longitude %s Latitude %s" % (caption, user_id, longitude, latitude))
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
		yonderdb.add_video(video.filename[:-4], caption, user_id, longitude, latitude)


class Feed(object):

	def get_videos(self, user_id, longitude, latitude):
		radius = float(10);
		longitude = float(longitude)
		latitude = float(latitude)
		rlon1 = longitude - (radius / abs(math.cos(math.radians(latitude)) * 69))
		rlon2 = longitude + (radius / abs(math.cos(math.radians(latitude)) * 69))
		rlat1 = latitude - (radius / 69)
		rlat2 = latitude + (radius / 69)
		yonderdb = YonderDb()
		video_ids = yonderdb.get_videos(user_id, longitude, latitude, rlon1, rlon2, rlat1, rlat2)
		yonderdb.add_seen(user_id, video_ids)
		yonderdb.update_last_request(user_id) # Keep it client side?
		return video_ids

	def get_videos_info(self, ids):
		video_ids = ids.split("xxx")
		yonderdb = YonderDb()
		videos_info = []
		if len(video_ids) > 0:
			videos_info = yonderdb.get_video_info(video_ids)
		return videos_info


class Video(object):
	def add_flag(self, video_id):
		yonderdb = YonderDb()
		yonderdb.flag_video(video_id)

	def add_rating(self, video_id, rating):
		yonderdb = YonderDb()
		yonderdb.rate_video(video_id, int(rating))
