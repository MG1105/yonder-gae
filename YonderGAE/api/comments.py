from db import YonderDb

class Comment (object):

	def add_comment(self, nickname, comment_id, comment, video_id, user_id):
		yonderdb = YonderDb()
		caption = yonderdb.add_comment(nickname, comment_id, comment, video_id, user_id)
		from util import User
		if user_id != "897d1e5hb8u47u56jh6":
			email_body = "Caption: '%s' Comment '%s' User %s" % (caption, comment, user_id)
			User.email("New Comment", email_body)

	def get_comments(self, video_id):
		yonderdb = YonderDb()
		comment_list = yonderdb.get_comments(video_id)
		return comment_list

	def add_flag(self, comment_id, user_id):
		yonderdb = YonderDb()
		yonderdb.flag_comment(comment_id, user_id)

	def rate_comment(self, comment_id, rating, user_id):
		yonderdb = YonderDb()
		yonderdb.rate_comment(comment_id, rating, user_id)