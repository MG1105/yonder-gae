import logging
import webapp2
import json
from videos import Upload
from videos import Story
from videos import Feed
from channels import Channels
from notifications import Notifications
from comments import Comment
from videos import Video
from util import User
from cron import Cron

class Videos(webapp2.RequestHandler):

	def post(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			video = self.request.POST.multi["videofile"]
			thumbnail = self.request.POST.multi["videothumbnail"]
			caption = self.request.get("caption")
			user_id = self.request.get("user")
			channel = self.request.get("channel")
			upload = Upload()
			upload.add_video(video, thumbnail, caption, user_id, channel)
		except Exception:
			logging.exception("Failed uploading the video")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Video uploaded successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

	def get(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.GET["user"]
			feed = Story()
			if "channel" in  self.request.GET:
				channel = self.request.GET["channel"]
				channel_sort = self.request.GET["channel_sort"]
				video_ids = feed.get_videos(user_id, channel, channel_sort)
			if "video" in  self.request.GET:
				video = self.request.GET["video"]
				video_ids = feed.get_video(user_id, video)
		except Exception:
			logging.exception("Failed looking for videos")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Video Ids retrieved successfully")
			out = {"success": 1, "videos": video_ids}
			self.response.write(json.dumps(out))

class VideosInfo(webapp2.RequestHandler):

	def get(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			ids = self.request.GET["ids"] # could reach a limit?
			video_ids = ids.split("xxx")
			feed = Story()
			videos_info = feed.get_videos_info(video_ids)
		except Exception:
			logging.exception("Failed looking for videos")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Video Ids retrieved successfully")
			out = {"success": 1, "videos": videos_info}
			self.response.write(json.dumps(out))

class Comments(webapp2.RequestHandler):

	def post(self, video_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.POST["user"]
			nickname = self.request.POST["nickname"]
			text = self.request.POST["comment"]
			comment = Comment()
			id = comment.add_comment(nickname, text, video_id, user_id)
		except Exception:
			logging.exception("Failed to add a comment")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Comment added successfully")
			out = {"success": 1, "comment_id":id}
			self.response.write(json.dumps(out))

	def get(self, video_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.get("user")
			comment = Comment()
			comment_list = comment.get_comments(video_id, user_id)
		except Exception:
			logging.exception("Failed getting comments")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Comments retrieved successfully")
			out = {"success": 1, "comments": comment_list}
			self.response.write(json.dumps(out))

class ReportVideo(webapp2.RequestHandler):

	def post(self, video_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.POST["user"]
			report = Video()
			report.add_flag(video_id, user_id)
		except Exception:
			logging.exception("Failed to report video %s" % video_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Video reported successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class ReportComment(webapp2.RequestHandler):

	def post(self, comment_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.POST["user"]
			comment = Comment()
			comment.add_flag(comment_id, user_id)
		except Exception:
			logging.exception("Failed to report comment %s" % comment_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Comment reported successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class RateComment(webapp2.RequestHandler):

	def post(self, comment_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			rating = self.request.POST["rating"]
			user_id = self.request.POST["user"]
			comment = Comment()
			comment.rate_comment(comment_id, rating, user_id)
		except Exception:
			logging.exception("Failed to rate comment %s" % comment_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Comment rated successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class RateChannel(webapp2.RequestHandler):

	def post(self, channel_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			rating = self.request.POST["rating"]
			user_id = self.request.POST["user"]
			channel = Channels()
			channel.rate_channel(channel_id, rating, user_id)
		except Exception:
			logging.exception("Failed to rate channel %s" % channel_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Channel rated successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class VideoRating(webapp2.RequestHandler):

	def post(self, video_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			rating = self.request.POST["rating"]
			user_id = self.request.POST["user"]
			video = Video()
			video.add_rating(video_id, rating, user_id)
		except Exception:
			logging.exception("Failed to add video rating")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Video rating added successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class Verify(webapp2.RequestHandler):

	def get(self, user_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user = User()
			version = self.request.get("version")
			user_info = user.verify(user_id, version)
		except Exception:
			logging.exception("Failed verifying user %s" % user_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("User info retrieved successfully")
			out = {"success": 1, "user": user_info}
			self.response.write(json.dumps(out))

class Ping(webapp2.RequestHandler):

	def get(self, user_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user = User()
			version = self.request.get("version")
			user.ping(user_id)
		except Exception:
			logging.exception("Failed ping user %s" % user_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.debug("User pinged successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class HomeFeed(webapp2.RequestHandler):

	def get(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.GET["user"]
			feed = Feed()
			videos = feed.get_videos(user_id)
		except Exception:
			logging.exception("Failed looking for feed videos")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Feed videos retrieved successfully")
			out = {"success": 1, "feed": videos}
			self.response.write(json.dumps(out))

class Channel(webapp2.RequestHandler):

	def get(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.GET["user"]
			sort = self.request.GET["sort"]
			channels = Channels()
			channels_list = channels.get_channels(user_id, sort)
		except Exception:
			logging.exception("Failed looking for channels")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Channels retrieved successfully")
			out = {"success": 1, "channels": channels_list}
			self.response.write(json.dumps(out))

	def post(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.POST["user"]
			channel_name = self.request.POST["channel"]
			channels = Channels()
			channels.add_channel(channel_name, user_id)
		except Exception:
			logging.exception("Failed to add a comment")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Channel added successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class Contact(webapp2.RequestHandler):

	def post(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.POST["user"]
			message = self.request.POST["message"]
			reply_to = self.request.POST["reply_to"]
			User.email("Contact Us message from %s" % user_id, message, reply_to)
		except Exception:
			logging.exception("Failed to email message")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Email sent successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class Notification(webapp2.RequestHandler):

	def get(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			user_id = self.request.GET["user"]
			seen = self.request.GET["seen"]
			notifications = Notifications()
			notifications_list = notifications.get_notifications(user_id, seen)
		except Exception:
			logging.exception("Failed looking for notifications")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			if seen == 1:
				logging.info("Notifications retrieved successfully")
			out = {"success": 1, "notifications": notifications_list}
			self.response.write(json.dumps(out))

class CronJob(webapp2.RequestHandler):

	def get(self):
		cron = Cron()
		cron.run()

# Every request associated to user id
app = webapp2.WSGIApplication([(r"/cron", CronJob),
							   (r"/videos", Videos),
							   (r"/feed", HomeFeed),
							   (r"/channels", Channel),
							   (r"/contact", Contact),
							   (r"/channels/(\d+)/rating", RateChannel),
							   (r"/notifications", Notification),
                               (r"/videos/info", VideosInfo),
                               (r"/videos/(\d+)/comments", Comments),
                               (r"/videos/(\d+)/flag", ReportVideo),
                               (r"/comments/(\d+)/flag", ReportComment),
							   (r"/comments/(\d+)/rating", RateComment),
                               (r"/videos/(\d+)/rating", VideoRating),
                               (r"/users/(\w+)/ping", Ping),
                               (r"/users/(\w+)/verify", Verify)], debug=True)