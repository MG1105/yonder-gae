import logging
import webapp2
import json
from videos import Upload
from videos import Feed
from comments import Comment
from videos import Video
from util import User

class Videos(webapp2.RequestHandler):

	def post(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			video = self.request.POST.multi["uploadedfile"]
			caption = self.request.get("caption")
			user_id = self.request.get("user")
			longitude = self.request.get("long")
			latitude = self.request.get("lat")
			upload = Upload()
			upload.add_video(video, caption, user_id, longitude, latitude)
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
			longitude = self.request.GET["long"]
			latitude = self.request.GET["lat"]
			user_id = self.request.GET["user"]
			feed = Feed()
			video_ids = feed.get_videos(user_id, longitude, latitude)
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
			ids = self.request.GET["ids"]
			feed = Feed()
			videos_info = feed.get_videos_info(ids)
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
			text = self.request.POST["comment"]
			comment = Comment()
			comment.add_comment(text, video_id, user_id)
		except Exception:
			logging.exception("Failed to add a comment")
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Comment added successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

	def get(self, video_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			comment = Comment()
			comment_list = comment.get_comments(video_id)
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
			report = Video()
			report.add_flag(video_id)
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
			comment = Comment()
			comment.add_flag(comment_id)
		except Exception:
			logging.exception("Failed to report comment %s" % comment_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("Comment reported successfully")
			out = {"success": 1}
			self.response.write(json.dumps(out))

class VideoRating(webapp2.RequestHandler):

	def post(self, video_id):
		self.response.headers["Content-Type"] = "application/json"
		try:
			rating = self.request.POST["rating"]
			video = Video()
			video.add_rating(video_id, rating)
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
			user_info = user.verify(user_id)
		except Exception:
			logging.exception("Failed verifying user %s" % user_id)
			out = {"success": 0}
			self.response.write(json.dumps(out))
		else:
			logging.info("User info retrieved successfully")
			out = {"success": 1, "user": user_info}
			self.response.write(json.dumps(out))



app = webapp2.WSGIApplication([(r"/videos", Videos),
                               (r"/videos/info", VideosInfo),
                               (r"/videos/(\d+)/comments", Comments),
                               (r"/videos/(\d+)/flag", ReportVideo),
                               (r"/comments/(\d+)/flag", ReportComment),
                               (r"/videos/(\d+)/rating", VideoRating),
                               (r"/users/(\d+)/verify", Verify)], debug=True)