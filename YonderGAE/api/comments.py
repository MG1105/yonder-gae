from db import YonderDb

class Comment (object):

	def add_comment(self, nickname, comment, video_id, user_id):
		yonderdb = YonderDb()
		id = yonderdb.add_comment(nickname, comment, video_id, user_id)
		return id

	def get_comments(self, video_id, user_id):
		yonderdb = YonderDb()
		comment_list = yonderdb.get_comments(video_id, user_id)
		return comment_list

	def rate_comment(self, comment_id, rating, user_id):
		yonderdb = YonderDb()
		yonderdb.rate_comment(comment_id, rating, user_id)