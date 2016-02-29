import cloudstorage as gcs
import logging
import math
from db import YonderDb
from random import randint

class Notifications(object):

	def get_notifications(self, user_id, seen):
		yonderdb = YonderDb()
		notification_list = []
		ts = '2015-12-26 05:49:27' # keep ts in table, last time user opened notifications
		video_votes = yonderdb.get_video_votes(user_id, ts)
		comment_votes = yonderdb.get_comment_votes(user_id, ts)
		channel_votes = yonderdb.get_channel_votes(user_id, ts)
		channel_removed = yonderdb.get_channel_removed(user_id, ts)
		for row in video_votes:
			name = row["caption"][:50]
			content = str(row["count"]) + ' more people voted on your video "' + name + '"\n'
			content += "Channel: " + row["channel"]
			notification_list.append({"content": content, "video_id": row["video_id"]})
		for row in comment_votes:
			name = row["comment"][:50]
			content = str(row["count"]) + ' more people voted on your comment "' + name + '"\n'
			content += "Video: " + row["caption"] + "\n"
			content += "Channel: " + row["channel"]
			notification_list.append({"content": content, "channel_id": 1, "video_id": row["video_id"]})
		for row in channel_votes:
			name = row["name"]
			content = str(row["count"]) + ' more people voted on your channel "' + name + '"\n'
			notification_list.append({"content": content, "channel_id": "1", "video_id": ""})
		for row in channel_removed:
			name = row["name"]
			content = "Channel %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": ""})
		return notification_list
