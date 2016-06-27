import cloudstorage as gcs
import logging
import math
from db import YonderDb
from random import randint

class Notifications(object):

	def get_notifications(self, user_id, seen):
		yonderdb = YonderDb()
		notification_list = []
		ts = yonderdb.get_last_notification_seen_ts(user_id, seen)

		video_votes = yonderdb.get_video_votes(user_id, ts)
		comment_votes = yonderdb.get_comment_votes(user_id, ts)
		channel_votes = yonderdb.get_channel_votes(user_id, ts)

		channels_removed = yonderdb.get_channels_removed(user_id, ts)
		videos_removed = yonderdb.get_videos_removed(user_id, ts)
		comments_removed = yonderdb.get_comments_removed(user_id, ts)

		new_channel_videos = yonderdb.get_new_channel_videos(user_id, ts)
		new_video_comments = yonderdb.get_new_video_comments(user_id, ts)

		#other_video_replies = yonderdb.get_other_video_replies(user_id, ts)
		other_comment_replies = yonderdb.get_other_comment_replies(user_id, ts)

		gold_received = yonderdb.get_gold_received(user_id, ts)
		followers = yonderdb.get_followers(user_id, ts)

		# notification_list.append({"content": 'You received 3 Vidici Awards for your scene "Vidici Romance" on #LipSyncBattle', "channel_id": "", "video_id": "", "thumbnail_id" : "", "notification_id": 1})
		# notification_list.append({"content": '315 more people started following you', "channel_id": "", "video_id": "", "thumbnail_id" : "", "notification_id": 2})
		# notification_list.append({"content": '65 more people voted on your scene "Vidici Romance" on #LipSyncBattle', "channel_id": "", "video_id": "", "thumbnail_id" : "", "notification_id": 3})
		# notification_list.append({"content": '46 more people voted on your hashtag #LipSyncBattle', "channel_id": "", "video_id": "", "thumbnail_id" : "", "notification_id": 5})
		# notification_list.append({"content": '28 more comments were posted on your scene "Vidici Romance"', "channel_id": "", "video_id": "", "thumbnail_id" : "", "notification_id": 6})
		# notification_list.append({"content": '15 more scenes were added to your hashtag #LipSyncBattle', "channel_id": "", "video_id": "", "thumbnail_id" : "", "notification_id": 7})

		for row in gold_received:
			name = row["caption"][:50]
			if row["count"] == 1:
				content =  'You received 1 Vidici Award for your scene "' + name + '" on '
			else:
				content =  'You received %s Vidici Awards for your scene "' % row["count"] + name + '" on '
			content += "#" + row["channel"]
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"], "thumbnail_id" : row["thumbnail_id"], "notification_id": 1})

		if followers > 0:
			if followers == 1:
				content = str(followers) + " more person started following you"
			else:
				content = str(followers) + " more people started following you"
			notification_list.append({"content": content, "channel_id": "", "video_id": "", "thumbnail_id" : "", "notification_id": 2})

		for row in video_votes:
			name = row["caption"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more person voted on your scene "' + name + '" on '
			else:
				content = str(row["count"]) + ' more people voted on your scene "' + name + '" on '
			content += "#" + row["channel"]
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"], "thumbnail_id" : row["thumbnail_id"], "notification_id": 3})
		for row in comment_votes:
			name = row["comment"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more person voted on your comment "' + name + '" on '
			else:
				content = str(row["count"]) + ' more people voted on your comment "' + name + '" on '
			content += "scene " + row["caption"] + " on "
			content += "#" + row["channel"]
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"], "thumbnail_id" : row["thumbnail_id"], "notification_id": 4})
		for row in channel_votes:
			name = row["name"]
			if row["count"] == 1:
				content = str(row["count"]) + ' more person voted on your hashtag #' + name
			else:
				content = str(row["count"]) + ' more people voted on your hashtag #' + name
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": "", "thumbnail_id" : row["thumbnail_id"], "notification_id": 5})

		for row in new_video_comments:
			name = row["name"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more comment was posted on your scene "' + name + '"'
			else:
				content = str(row["count"]) + ' more comments were posted on your scene "' + name + '"'
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"], "thumbnail_id" : row["thumbnail_id"], "notification_id": 6})

		for row in new_channel_videos:
			name = row["name"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more scene was added to your hashtag #' + name
			else:
				content = str(row["count"]) + ' more scenes were added to your hashtag #' + name
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": "", "thumbnail_id" : "1466142952772", "notification_id": 7})

		for row in channels_removed:
			name = row["name"]
			content = "#%s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": "", "thumbnail_id" : row["thumbnail_id"], "notification_id": 8})
		for row in videos_removed:
			name = row["name"][:50]
			content = "Your scene %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": "", "thumbnail_id" : row["thumbnail_id"], "notification_id": 9})
		for row in comments_removed:
			name = row["name"][:50]
			content = "Your comment %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": "", "thumbnail_id" : row["thumbnail_id"], "notification_id": 10})

		# for row in other_video_replies:
		# 	name = row["name"][:50]
		# 	if row["count"] == 1:
		# 		content = str(row["count"]) + ' more reaction was posted on #' + name
		# 	else:
		# 		content = str(row["count"]) + ' more reactions were posted on #' + name
		# 	notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": ""})
		for row in other_comment_replies:
			name = row["name"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more comment was posted on scene "' + name + '"'
			else:
				content = str(row["count"]) + ' more comments were posted on scene "' + name + '"'
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"], "thumbnail_id" : row["thumbnail_id"], "notification_id": 11})


		return notification_list
