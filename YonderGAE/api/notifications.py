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
		other_video_replies = yonderdb.get_other_video_replies(user_id, ts)
		other_comment_replies = yonderdb.get_other_comment_replies(user_id, ts)


		for row in new_channel_videos:
			name = row["name"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more reaction was posted on your hashtag #' + name
			else:
				content = str(row["count"]) + ' more reactions were posted on your hashtag #' + name
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": ""})
		for row in new_video_comments:
			name = row["name"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more comment was posted on your reaction "' + name + '"'
			else:
				content = str(row["count"]) + ' more comments were posted on your reaction "' + name + '"'
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})

		for row in video_votes:
			name = row["caption"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more person voted on your reaction "' + name + '" on '
			else:
				content = str(row["count"]) + ' more people voted on your reaction "' + name + '" on '
			content += "#" + row["channel"]
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})
		for row in comment_votes:
			name = row["comment"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more person voted on your comment "' + name + '" on '
			else:
				content = str(row["count"]) + ' more people voted on your comment "' + name + '" on '
			content += "reaction " + row["caption"] + " on "
			content += "#" + row["channel"]
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})
		for row in channel_votes:
			name = row["name"]
			if row["count"] == 1:
				content = str(row["count"]) + ' more person voted on your hashtag #' + name
			else:
				content = str(row["count"]) + ' more people voted on your hashtag #' + name
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": ""})

		for row in channels_removed:
			name = row["name"]
			content = "#%s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": ""})
		for row in videos_removed:
			name = row["name"][:50]
			content = "Your reaction %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": ""})
		for row in comments_removed:
			name = row["name"][:50]
			content = "Your comment %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": ""})

		for row in other_video_replies:
			name = row["name"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more reaction was posted on #' + name
			else:
				content = str(row["count"]) + ' more reactions were posted on #' + name
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": ""})
		for row in other_comment_replies:
			name = row["name"][:50]
			if row["count"] == 1:
				content = str(row["count"]) + ' more comment was posted on reaction "' + name + '"'
			else:
				content = str(row["count"]) + ' more comments were posted on reaction "' + name + '"'
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})


		return notification_list
