from db import YonderDb
import logging

class Comment (object):

	def add_comment(self, comment, video_id, user_id):
		yonderdb = YonderDb()
		yonderdb.add_comment(comment, video_id, user_id)

	def get_comments(self, video_id):
		comment_list = []
		yonderdb = YonderDb()
		comment_list = yonderdb.get_comments(video_id)
		return comment_list
