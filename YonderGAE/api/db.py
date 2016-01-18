import MySQLdb
from datetime import datetime
from datetime import timedelta
import logging

adminkey = "897d1e5hb8u47u56jh6"

class YonderDb(object):

	def __init__(self):
		self.cur, self.conn = None, None

	def connect(self):
		self.conn = MySQLdb.connect(unix_socket="/cloudsql/subtle-analyzer-90706:yonder", user="root", db="yonderdb", charset="utf8")
		self.cur = self.conn.cursor()
		self.cur.execute("SET NAMES 'utf8mb4'")

	def execute(self, query):
		self.connect()
		logging.debug("Executing %s" % query)
		self.cur.execute(query)
		self.conn.commit()

	def add_video(self, video_id, caption, user_id, longitude, latitude, channel_id):
		rating, flag = 0, 0
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		caption = caption.replace("'", "\\'")
		query = "insert into videos values ('%s', '%s', '%s', '%s', %d, %d, 0, %s)" % (video_id, user_id, ts, caption, rating, flag, channel_id)
		self.execute(query)
		query = "insert into location values ('%s', point(%s,%s), 1)" % (video_id, longitude, latitude)
		self.execute(query)
		#self.update_score(video_id, True, "10")

	def get_videos(self, user_id, longitude, latitude, rlon1, rlon2, rlat1, rlat2, limit):
		query = "select L.video_id from yonderdb.location L " \
				"left join (select * from yonderdb.seen where user_id = '%s' ) AS S on L.video_id = S.video_id " \
				"left join yonderdb.videos as V on L.video_id = V.video_id " \
				"where S.user_id is NULL and L.visible = 1 and V.rating > -2 and st_within(location, envelope(linestring(point(%s, %s), point(%s, %s)))) " \
				"order by V.ts DESC limit %s;"
		# order by distance: order by st_distance(point(%s, %s), location)
		query = query % (user_id, rlon1, rlat1, rlon2, rlat2, limit)
		if user_id == adminkey:
			query = """select V.video_id from videos V join location L on V.video_id = L.video_id where L.visible = 1 order by V.ts DESC limit 3;"""
		self.execute(query)
		ids = [row[0] for row in self.cur.fetchall()]
		logging.info("Videos found: " + str(ids))
		return ids

	def get_my_videos(self, user_id, uploaded, commented):
		if uploaded:
			query = "select V.video_id from videos V join location L on V.video_id = L.video_id where V.user_id = '%s' and L.visible = 1 order by V.ts;" % user_id
			self.execute(query)
			ids = [row[0] for row in self.cur.fetchall()]
		if commented:
			ts = datetime.utcnow() - timedelta(hours = 24)
			query = "select distinct(C.video_id) from comments C join location L on C.video_id = L.video_id where " \
					"C.user_id = '%s' and L.visible = 1 and C.visible = 1 and C.ts > '%s' order by C.ts; " % (user_id, ts)
			self.execute(query)
			ids += [row[0] for row in self.cur.fetchall()]
		unique_ids = []
		for id in ids:
			if id not in unique_ids:
				unique_ids.append(id)
		logging.info("Videos found: " + str(unique_ids))
		return unique_ids

	def get_video_info(self, video_ids):
		info = []
		query = "select caption, rating, boost from videos where video_id = '%s'"
		comments_total_query = "select count(*) from comments where video_id = '%s' and visible = 1"
		for id in video_ids:
			self.execute(query % id)
			row = self.cur.fetchone()
			if row[2] is None:
				boost = 0
			else:
				boost = row[2]
			stats = {"id": id, "caption": row[0], "rating": row[1] + boost}
			self.execute(comments_total_query % id)
			row = self.cur.fetchone()
			stats["comments_total"] = row[0]
			info.append(stats)
		logging.debug(str(info))
		return info

	def update_last_request(self, user_id, version):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into users values ('%s', NULL, '%s', NULL, NULL, 0, '%s', NULL) on duplicate key update last_request = values(last_request)" % (user_id, ts, ts)
		self.execute(query)
		if self.cur.rowcount == 1:
			from util import User
			email_body = "User %s" % (user_id)
			User.email("New User", email_body)
		query = "update users set version=%s where user_id = '%s'" % (version, user_id)
		self.execute(query)

	def update_last_ping(self, user_id):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into users values ('%s', '%s', NULL, NULL, NULL, 0, '%s', NULL) on duplicate key update last_ping = values(last_ping)" % (user_id, ts, ts)
		self.execute(query)


	def add_seen(self, user_id, video_ids):
		if user_id == adminkey:
			return
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		for id in video_ids:
			query = "insert into seen values ('%s','%s', '%s')" % (user_id, id, ts)
			self.execute(query)

	def recently_seen(self, user_id, hours):
		if user_id == adminkey:
			return 0
		past = datetime.utcnow() - timedelta(hours = hours)
		ts = past.strftime("%Y-%m-%d %H:%M:%S")
		query = "select video_id from seen where user_id = '%s' and ts > '%s'" % (user_id, ts)
		self.execute(query)
		recent = self.cur.rowcount
		return recent

	def add_comment(self, nickname, comment_id, comment, video_id, user_id):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		comment = comment.replace("'", "\\'")
		query = "insert into comments values ('%s', '%s', '%s', '%s', '%s', 0, 0, 1, '%s')" % (comment_id, comment, video_id, user_id, nickname, ts)
		self.execute(query)
		query = "select caption from videos where video_id = '%s'" % video_id
		self.execute(query)
		row = self.cur.fetchone()
		caption = row[0]
		return caption

	def get_comments(self, video_id):
		comment_list = []
		query = "select comment_id, comment, rating, nickname from comments where video_id = '%s' and visible = 1 order by ts" % video_id
		self.execute(query)
		for row in self.cur.fetchall():
			comment = {"id": row[0].decode(encoding='UTF-8',errors='strict'), "content": row[1], "rating":row[2], "nickname":row[3]}
			comment_list.append(comment)
		return comment_list

	def flag_video(self, video_id, user_id):
		query = "update videos set flag=flag+1 where video_id = '%s'" % video_id
		if user_id == adminkey:
			query = "update location set visible=0 where video_id = '%s'" % video_id
		self.execute(query)

	def flag_comment(self, comment_id, user_id):
		query = "update comments set flag=flag+1 where comment_id = '%s'" % comment_id
		if user_id == adminkey:
			query = "update comments set visible=0 where comment_id = '%s'" % comment_id
		self.execute(query)

	def rate_comment(self,comment_id, rating, user_id):
		if user_id == adminkey:
			from random import randint
			if rating == "1":
				rating = 3
			elif rating == "-1":
				rating = -3
		self.update_score(comment_id, False,rating)
		query = "update comments set rating=rating+(%s) where comment_id = '%s'" % (rating,comment_id)
		self.execute(query)

	def rate_video(self,video_id, rating, user_id):
		if user_id == adminkey:
			from random import randint
			if rating == 1:
				rating = 3
			elif rating == -1:
				rating = -3
		self.update_score(video_id, True, rating)
		query = "update videos set rating=rating+(%s) where video_id = '%s'" % (rating,video_id)
		self.execute(query)

	def get_user_info(self, user_id, upgrade):
		query = "select warn, ban from users where user_id = '%s'" % user_id
		self.execute(query)
		row = self.cur.fetchone()
		if row is not None:
			info = {"warn": row[0], "ban": row[1], "upgrade": upgrade}
		else:
			logging.error("Cannot find user info")
		return info

	def user_warned(self, user_id):
		query = "update users set warn=0 where user_id = '%s'" % user_id
		self.execute(query)

	def cleanup(self, admin = False):
		if admin:
			oldest = datetime.utcnow() - timedelta(hours = 9000)
			ts = oldest.strftime("%Y-%m-%d %H:%M:%S")
			admin_condition = " and V.user_id = '%s'" % adminkey
		else:
			oldest = datetime.utcnow() - timedelta(hours = 24)
			ts = oldest.strftime("%Y-%m-%d %H:%M:%S")
			admin_condition = " and V.user_id != '%s'" % adminkey
		query = "select video_id from videos V where V.ts < '%s'" % ts + admin_condition
		self.execute(query)
		ids = []
		for row in self.cur.fetchall():
			ids.append(row[0])
		if len(ids) > 0:
			query = "Delete C FROM videos V join comments C on V.video_id = C.video_id where V.ts < '%s'" % ts + admin_condition
			self.execute(query)
			query = "Delete L FROM videos V join location L on V.video_id = L.video_id where V.ts < '%s'" % ts + admin_condition
			self.execute(query)
			query = "Delete S FROM videos V join seen S on V.video_id = S.video_id where V.ts < '%s'" % ts + admin_condition
			self.execute(query)
			query = "Delete V from videos V where V.ts < '%s'" % ts + admin_condition
			self.execute(query)
		return ids

	def flag_check(self):
		query = "update comments set visible=-1 where flag > 3"
		self.execute(query)

	def fake_rating(self):
		query = "select video_id from videos where boost = 0 and user_id = '%s'" % adminkey
		self.execute(query)
		from random import randint
		for row in self.cur.fetchall():
			points = randint(10,30)
			query = "update videos set boost = boost +(%s) where video_id = '%s'" % (points, row[0])
			self.execute(query)
			self.update_score(row[0], True, points)

	def update_score(self, id, video, points): # no local commit
		if video:
			user_id_query = "select user_id from videos where video_id = '%s'" % (id)
		else:
			user_id_query = "select user_id from comments where comment_id = '%s'" % (id)

		self.execute(user_id_query)
		row = self.cur.fetchone()
		if row is not None:
			user_id = row[0]
			query = "update users set score=score+(%s) where user_id = '%s'" % (points,user_id)
			self.execute(query)
		else:
			logging.error("Cannot update user score")

	def get_score(self, user_id):
		query = "select score from users where user_id = '%s'" % user_id
		self.execute(query)
		row = self.cur.fetchone()
		score = 0
		if row is not None:
			score = row[0]
		else:
			logging.error("Cannot find user score")
		return score

	def get_channels(self, user_id, sort):
		channel_list = []
		query = "select channel_id, name from channels"
		if sort == "new":
			query = "select channel_id, name from channels limit 1"
		self.execute(query)
		for row in self.cur.fetchall():
			logging.debug(row[0])
			channel = {"id": row[0], "name": row[1]}
			channel_list.append(channel)
		return channel_list

	def get_video_votes(self, user_id, ts):
		video_vote_list = []
		query = "SELECT count(*) as count, caption, video_id FROM votes join videos on video_id = item_id " \
				"where item = 'video' and videos.user_id = '%s' and votes.ts > '%s' group by item_id;" % (user_id, ts)
		self.execute(query)
		for row in self.cur.fetchall():
			query = "select channels.name from videos join channels on videos.channel_id = channels.channel_id where video_id = '%s'" % (row[2])
			self.execute(query)
			info = self.cur.fetchone()
			video_vote_list.append({"count": row[0], "caption": row[1], "channel": info[0]})
		return video_vote_list

	def get_comment_votes(self, user_id, ts):
		comment_vote_list = []
		query = "SELECT count(*) as count, comment, video_id FROM votes join comments on comment_id = item_id " \
				"where item = 'comment' and comments.user_id = '%s' and votes.ts > '%s' group by item_id;" % (user_id, ts)
		self.execute(query)
		for row in self.cur.fetchall():
			query = "select caption, channels.name from videos join channels on videos.channel_id = channels.channel_id where video_id = '%s'" % (row[2])
			self.execute(query)
			info = self.cur.fetchone()
			comment_vote_list.append({"count": row[0], "comment": row[1],"caption": info[0], "channel": info[1]})

		return comment_vote_list

	def get_channel_votes(self, user_id, ts):
		channel_vote_list = []
		query = "SELECT count(*) as count, name FROM votes join channels on channel_id = item_id " \
				"where item = 'channel' and channels.user_id = '%s' and votes.ts > '%s' group by item_id;" % (user_id, ts)
		self.execute(query)
		for row in self.cur.fetchall():
			channel_vote_list.append({"count": row[0], "name": row[1]})
		return channel_vote_list






















