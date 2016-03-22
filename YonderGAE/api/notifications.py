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

		for row in video_votes:
			name = row["caption"][:50]
			content = str(row["count"]) + ' more people voted on your video "' + name + '"\n'
			content += "Channel: " + row["channel"]
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})
		for row in comment_votes:
			name = row["comment"][:50]
			content = str(row["count"]) + ' more people voted on your comment "' + name + '"\n'
			content += "Video: " + row["caption"] + "\n"
			content += "Channel: " + row["channel"]
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})
		for row in channel_votes:
			name = row["name"]
			content = str(row["count"]) + ' more people voted on your channel "' + name + '"\n'
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": ""})
		for row in channels_removed:
			name = row["name"]
			content = "Channel %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": ""})
		for row in videos_removed:
			name = row["name"][:50]
			content = "Video %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": ""})
		for row in comments_removed:
			name = row["name"][:50]
			content = "Comment %s received 5 downvotes and was removed" % name
			notification_list.append({"content": content, "channel_id": "", "video_id": ""})
		for row in new_channel_videos:
			name = row["name"][:50]
			content = str(row["count"]) + ' more videos posted to your channel "' + name + '"\n'
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": ""})
		for row in new_video_comments:
			name = row["name"][:50]
			content = str(row["count"]) + ' more comments on your video "' + name + '"\n'
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})
		for row in other_video_replies:
			name = row["name"][:50]
			content = str(row["count"]) + ' more videos posted to channel "' + name + '"\n'
			notification_list.append({"content": content, "channel_id": row["channel_id"], "video_id": ""})
		for row in other_comment_replies:
			name = row["name"][:50]
			content = str(row["count"]) + ' more comments on video "' + name + '"\n'
			notification_list.append({"content": content, "channel_id": "", "video_id": row["video_id"]})


		return notification_list
