import logging
import webapp2
import json
from videos import Upload
from videos import Feed
from comments import Comment

class Videos(webapp2.RequestHandler):

	def post(self):
		self.response.headers["Content-Type"] = "application/json"
		try:
			video = self.request.POST.multi["uploadedfile"]
			caption = self.request.POST.multi["caption"]
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
			videos_info = feed.get_videos(user_id, longitude, latitude)
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




app = webapp2.WSGIApplication([(r"/videos", Videos),
                               (r"/videos/(\d+)/comments", Comments)], debug=True)