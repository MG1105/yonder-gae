import MySQLdb
from datetime import datetime
import logging

class YonderDb(object):

	def __init__(self):
		self.cur, self.conn = None, None

	def connect(self):
		self.conn = MySQLdb.connect(unix_socket="/cloudsql/subtle-analyzer-90706:yonder", user="root", db="yonderdb")
		self.cur = self.conn.cursor()

	def add_video(self, video_id, caption, user_id, longitude, latitude):
		rating, flag = 0, 0
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		self.connect()
		query = "insert into videos values ('%s', '%s', '%s', '%s', %d, %d)" % (video_id, user_id, ts, caption, rating, flag)
		self.cur.execute(query)
		logging.debug("Executing %s" % query)
		query = "insert into location values ('%s', point(%s,%s))" % (video_id, longitude, latitude)
		self.cur.execute(query)
		logging.debug("Executing %s" % query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def get_videos(self, user_id, longitude, latitude, rlon1, rlon2, rlat1, rlat2):
		query = """select L.video_id from yonderdb.location L left join (select * from yonderdb.seen where user_id = "%s" ) AS S on L.video_id = S.video_id
		where S.user_id is NULL and st_within(location, envelope(linestring(point(%s, %s), point(%s, %s))))	order by st_distance(point(%s, %s), location) limit  10;""" # limit 5 to 10 randomly
		self.connect()
		self.cur.execute(query % (user_id, rlon1, rlat1, rlon2, rlat2, longitude, latitude))
		logging.debug("Executing " + query % (user_id, rlon1, rlat1, rlon2, rlat2, longitude, latitude))
		ids = [row[0] for row in self.cur.fetchall()]
		self.cur.close()
		self.conn.close()
		logging.info("Videos found: " + str(ids))
		return ids

	def get_video_info(self, video_ids):
		info = []
		self.connect()
		query = "select caption, rating from videos where video_id = '%s'"
		comments_total_query = "select count(*) from comments where video_id = '%s' and visible = 1"
		for id in video_ids:
			self.cur.execute(query % id)
			row = self.cur.fetchone()
			stats = {"id": id, "caption": row[0], "rating": row[1]}
			self.cur.execute(comments_total_query % id)
			row = self.cur.fetchone()
			stats["comments_total"] = row[0]
			info.append(stats)
		self.cur.close()
		self.conn.close()
		logging.debug(str(info))
		return info

	def update_last_request(self, user_id):
		self.connect()
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into users values ('%s', '%s', NULL, NULL) on duplicate key update last_request = values(last_request)" % (user_id, ts)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()


	def add_seen(self, user_id, video_ids):
		self.connect()
		for id in video_ids:
			query = "insert into seen values ('%s','%s')" % (user_id, id)
			self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def add_comment(self, comment, video_id, user_id):
		self.connect()
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into comments values (NULL, '%s', '%s', '%s', 0, 1, '%s')" % (comment, video_id, user_id, ts)
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def get_comments(self, video_id):
		comment_list = []
		query = "select comment_id, comment from comments where video_id = '%s' and visible = 1" % video_id
		self.connect()
		self.cur.execute(query)
		logging.debug("Executing " + query)
		for row in self.cur.fetchall():
			comment = {"id": row[0], "content": row[1]}
			comment_list.append(comment)
		self.cur.close()
		self.conn.close()
		return comment_list

	def flag_video(self, video_id):
		self.connect()
		query = "update videos set flag=flag+1 where video_id = '%s'" % video_id
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def flag_comment(self, comment_id):
		self.connect()
		query = "update comments set flag=flag+1 where comment_id = '%s'" % comment_id
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def rate_video(self,video_id, rating):
		self.connect()
		query = "update videos set rating=rating+(%s) where video_id = '%s'" % (rating,video_id)
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def get_user_info(self, user_id):
		query = "select warn, ban from users where user_id = '%s'" % user_id
		self.connect()
		self.cur.execute(query)
		logging.debug("Executing " + query)
		row = self.cur.fetchone()
		if row is not None:
			info = {"warn": row[0], "ban": row[1]}
		else:
			query = "insert into users values ('%s', NULL, NULL, NULL)" % user_id
			self.cur.execute(query)
			self.conn.commit()
			info = {"warn": None, "ban": None}
		return info

	def user_warned(self, user_id):
		self.connect()
		query = "update users set warn=0 where user_id = '%s'" % user_id
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()



# Test caption and comments with quotes
# Cron job to delete videos > 24H every hour