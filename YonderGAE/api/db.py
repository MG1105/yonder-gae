import MySQLdb
from datetime import datetime
import logging

adminkey = "897d1e5hb8u47u56jh6"

class YonderDb(object):

	def __init__(self):
		self.cur, self.conn = None, None

	def connect(self):
		self.conn = MySQLdb.connect(unix_socket="/cloudsql/subtle-analyzer-90706:yonder", user="root", db="yonderdb", charset="utf8")
		self.cur = self.conn.cursor()
		self.cur.execute("SET NAMES 'utf8mb4'")

	def add_video(self, video_id, caption, user_id, longitude, latitude):
		rating, flag = 0, 0
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		self.connect()
		caption = caption.replace("'", "\\'")
		query = "insert into videos values ('%s', '%s', '%s', '%s', %d, %d)" % (video_id, user_id, ts, caption, rating, flag)
		self.cur.execute(query)
		logging.debug("Executing %s" % query)
		query = "insert into location values ('%s', point(%s,%s), 1)" % (video_id, longitude, latitude)
		self.cur.execute(query)
		logging.debug("Executing %s" % query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def get_videos(self, user_id, longitude, latitude, rlon1, rlon2, rlat1, rlat2, limit):
		query = """select L.video_id from yonderdb.location L left join (select * from yonderdb.seen where user_id = "%s" ) AS S on L.video_id = S.video_id
		where S.user_id is NULL and L.visible = 1 and st_within(location, envelope(linestring(point(%s, %s), point(%s, %s))))	order by st_distance(point(%s, %s), location) limit  %s;"""
		query = query % (user_id, rlon1, rlat1, rlon2, rlat2, longitude, latitude, limit)
		if user_id == adminkey:
			query = """select V.video_id from videos V join location L on V.video_id = L.video_id where L.visible = 1 order by V.ts DESC;"""
		self.connect()
		self.cur.execute(query)
		logging.debug("Executing " + query) # log first
		ids = [row[0] for row in self.cur.fetchall()]
		self.cur.close()
		self.conn.close()
		logging.info("Videos found: " + str(ids))
		return ids

	def get_my_videos(self, user_id, uploaded, commented):
		self.connect()
		if uploaded:
			query = "select V.video_id from videos V join location L on V.video_id = L.video_id where V.user_id = '%s' and L.visible = 1 order by V.ts;" % user_id
			self.cur.execute(query)
			logging.debug("Executing " + query)
			ids = [row[0] for row in self.cur.fetchall()]
		if commented:
			query = "select distinct(C.video_id) from comments C join location L on C.video_id = L.video_id where C.user_id = '%s' and L.visible = 1 and C.visible = 1 order by C.ts; " % user_id
			self.cur.execute(query)
			logging.debug("Executing " + query)
			ids += [row[0] for row in self.cur.fetchall()]
		unique_ids = []
		for id in ids:
			if id not in unique_ids:
				unique_ids.append(id)
		self.cur.close()
		self.conn.close()
		logging.info("Videos found: " + str(unique_ids))
		return unique_ids

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

	def add_comment(self, nickname, comment_id, comment, video_id, user_id):
		self.connect()
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		comment = comment.replace("'", "\\'")
		query = "insert into comments values ('%s', '%s', '%s', '%s', '%s', 0, 0, 1, '%s')" % (comment_id, comment, video_id, user_id, nickname, ts)
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def get_comments(self, video_id):
		comment_list = []
		query = "select comment_id, comment, rating, nickname from comments where video_id = '%s' and visible = 1 order by ts" % video_id
		self.connect()
		self.cur.execute(query)
		logging.debug("Executing " + query)
		for row in self.cur.fetchall():
			comment = {"id": row[0].decode(encoding='UTF-8',errors='strict'), "content": row[1], "rating":row[2], "nickname":row[3]}
			comment_list.append(comment)
		self.cur.close()
		self.conn.close()
		return comment_list

	def flag_video(self, video_id, user_id):
		self.connect()
		query = "update videos set flag=flag+1 where video_id = '%s'" % video_id
		if user_id == adminkey:
			query = "update location set visible=0 where video_id = '%s'" % video_id
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def flag_comment(self, comment_id, user_id):
		self.connect()
		query = "update comments set flag=flag+1 where comment_id = '%s'" % comment_id
		if user_id == adminkey:
			query = "update comments set visible=0 where comment_id = '%s'" % comment_id
		logging.debug("Execute: " + query)
		self.cur.execute(query)
		self.conn.commit()
		self.cur.close()
		self.conn.close()

	def rate_comment(self,comment_id, rating):
		self.connect()
		query = "update comments set rating=rating+(%s) where comment_id = '%s'" % (rating,comment_id)
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
			info = {"warn": row[0], "ban": row[1], "upgrade": 0}
		else:
			query = "insert into users values ('%s', NULL, NULL, NULL)" % user_id
			self.cur.execute(query)
			self.conn.commit()
			info = {"warn": None, "ban": None, "upgrade": 0}
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