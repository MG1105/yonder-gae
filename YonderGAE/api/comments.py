from db import YonderDb

class Comment (object):

	def add_comment(self, nickname, comment_id, comment, video_id, user_id):
		yonderdb = YonderDb()
		yonderdb.add_comment(nickname, comment_id, comment, video_id, user_id)

	def get_comments(self, video_id):
		yonderdb = YonderDb()
		comment_list = yonderdb.get_comments(video_id)
		return comment_list

	def add_flag(self, comment_id, user_id):
		yonderdb = YonderDb()
		yonderdb.flag_comment(comment_id, user_id)

	def rate_comment(self, comment_id, rating):
		yonderdb = YonderDb()
		yonderdb.rate_comment(comment_id, rating)