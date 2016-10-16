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

	def add_video(self, video_id, caption, user_id, channel_id, college):
		rating = 0
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		caption = caption.replace("'", "\\'")
		query = "insert into videos (video_id, user_id, ts, caption, channel_id, college_admin) values ('%s', '%s', '%s', '%s', %s, '%s')" % (video_id, user_id, ts, caption, channel_id, college)
		self.execute(query)
		#self.update_score(video_id, True, "10")

	def add_comment(self, comment, video_id, user_id):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		comment = comment.replace("'", "\\'")
		query = "insert into comments (comment, video_id, user_id, ts) values ('%s', '%s', '%s', '%s')" % (comment, video_id, user_id, ts)
		self.execute(query)
		return self.cur.lastrowid

	def add_channel(self, channel, user_id, nsfw):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		channel = MySQLdb.escape_string(channel)
		query = "insert into channels (name, user_id, ts, nsfw) values ('%s', '%s', '%s', %s)" % (channel, user_id, ts, nsfw)
		self.execute(query)

	def get_videos(self, user_id, channel, channel_sort):
		# channel_sort hot new top notification
		if channel_sort == "hot" or channel_sort == "new" or channel_sort == "top" or channel_sort == "notification":
			query = "select video_id from videos where channel_id = '%s' and visible = 1 order by ts"
		query = query % (channel)
		self.execute(query)
		ids = [row[0] for row in self.cur.fetchall()]
		logging.info("Videos found: " + str(ids))
		return ids

	def get_video_info(self, video_ids, user_id):
		info = []
		query = "select caption, V.rating, boost, C.name, V.user_id, V.gold, V.college_admin from videos V join channels C on V.channel_id = C.channel_id where V.video_id = '%s'"
		comments_total_query = "select count(*) from comments where video_id = '%s' and visible = 1"
		username_query = "select username, college from users where user_id = '%s'"
		for id in video_ids:
			rated = self.get_rated('video', id, user_id)
			self.execute(query % id)
			row = self.cur.fetchone()
			if row[2] is None:
				boost = 0
			else:
				boost = row[2]
			stats = {"id": id, "caption": row[0], "rating": row[1] + boost, "rated": rated, "channel_name": row[3], "gold": row[5]}
			college_admin = row[6]
			profile_id = row[4]
			self.execute(comments_total_query % id)
			row = self.cur.fetchone()
			stats["comments_total"] = row[0]
			self.execute(username_query % profile_id)
			row = self.cur.fetchone()
			stats["username"] = row[0]
			if profile_id == adminkey:
				stats["college"] = college_admin
				if stats["college"] is None:
					import random
					colleges = ["Arizona State", "Penn State", "University of Iowa", "University of Illinois", "University of Georgia", "Louisiana State", "University of Colorado", "Iowa State", "University of Wisconsin", "Tulane University", "West Virginia University", "Florida State"]
					stats["college"] = random.choice(colleges)
			else:
				stats["college"] = row[1]
			stats["user_id"] = profile_id
			info.append(stats)
		return info

	def get_feed_videos(self, user_id, type):
		info = []
		comments_total_query = "select count(*) from comments where video_id = '%s' and visible = 1"

		if type == "recent":
			query = "select V.video_id, caption, V.rating, boost, (select name from channels C where C.channel_id = V.channel_id) as name, " \
					"(select username from users U where V.user_id = U.user_id) as username, unix_timestamp(V.ts) from videos V where V.user_id = '%s' and V.visible = 1 order by V.ts DESC limit 20;"
		elif type == "home":
			query = "select V.video_id, caption, V.rating, boost, (select name from channels C where C.channel_id = V.channel_id) as name, " \
					"(select username from users U where V.user_id = U.user_id) as username, unix_timestamp(V.ts) from " \
					"(select following from follow where follower = '%s') as F left join videos V on F.following = V.user_id where V.visible = 1 order by V.ts DESC limit 20;"
		self.execute(query % user_id)
		for row in self.cur.fetchall():
			if row[3] is None:
				boost = 0
			else:
				boost = row[3]
			stats = {"video_id": row[0], "caption": row[1], "rating": row[2] + boost, "channel_name": row[4], "channel_id":"", "username": row[5], "thumbnail_id":row[0], "ts":row[6]}
			self.execute(comments_total_query % row[0])
			row = self.cur.fetchone()
			stats["comments_count"] = row[0]
			info.append(stats)
		return info

	def get_comments(self, video_id, user_id):
		comment_list = []
		query = "select comment_id, comment, rating, (select username from users U where U.user_id = C.user_id) as username from comments C where video_id = '%s' and visible = 1 order by ts" % video_id
		self.execute(query)
		for row in self.cur.fetchall():
			rated = self.get_rated('comment', row[0], user_id)
			comment = {"id": str(row[0]), "content": row[1], "rating":row[2], "username":row[3], "rated":rated}
			comment_list.append(comment)
		return comment_list

	def get_channels(self, user_id, sort):
		query = "select visits, install_date from users where user_id = '%s'" % user_id
		self.execute(query)
		row = self.cur.fetchone()
		if row is None:
			visits = 1
			installed =  datetime.utcnow()
		else:
			visits = row[0]
			installed = row[1]
		cut_off = datetime.strptime("2016-08-28 00:00:00", "%Y-%m-%d %H:%M:%S")
		channel_list = []
		if sort == "new":
			query = "select C.channel_id, C.name, sum(IFNULL(V.rating, 0)) + C.rating + sum(IFNULL(V.boost, 0)) as rating, count(V.video_id) as videos, " \
					"(select username from users U where C.user_id = U.user_id) as username, unix_timestamp(C.ts), nsfw from channels C left join videos V on C.channel_id = V.channel_id and V.visible = 1 and V.rating >= 0 " \
					"where C.visible = 1 and C.ts > (now() - INTERVAL 1 DAY) group by C.channel_id order by C.ts DESC limit 10"
		elif sort == "top":
			query = "select C.channel_id, C.name, sum(IFNULL(V.rating, 0)) + C.rating + sum(IFNULL(V.boost, 0)) as rating, count(V.video_id) as videos, " \
					"(select username from users U where C.user_id = U.user_id) as username, unix_timestamp(C.ts), nsfw from channels C left join videos V on C.channel_id = V.channel_id and V.visible = 1 and V.rating >= 0 " \
					"where C.visible = 1 and C.ts > (now() - INTERVAL 1 DAY) group by C.channel_id order by rating DESC limit 10"
		else:
			query = "select C.channel_id, C.name, sum(IFNULL(V.rating, 0)) + C.rating + sum(IFNULL(V.boost, 0)) as rating, count(V.video_id) as videos, " \
					"(select username from users U where C.user_id = U.user_id) as username, unix_timestamp(C.ts), nsfw from channels C right join videos V on C.channel_id = V.channel_id and V.visible = 1 and V.rating >= 0 " \
					"where C.visible = 1 and C.ts > (now() - INTERVAL 1 DAY) group by C.channel_id order by C.hot_score DESC limit 10"

		if user_id == "10206282032162320":
			query = "select C.channel_id, C.name, sum(IFNULL(V.rating, 0)) + C.rating + sum(IFNULL(V.boost, 0)) as rating, count(V.video_id) as videos, " \
					"(select username from users U where C.user_id = U.user_id) as username, unix_timestamp(C.ts), nsfw from channels C left join videos V on C.channel_id = V.channel_id and V.visible = 1 and V.rating >= 0 " \
					"where C.visible = 1 and C.ts > (now() - INTERVAL 30 DAY) group by C.channel_id order by rating DESC limit 50"
		self.execute(query)
		for row in self.cur.fetchall():
			rated = self.get_rated('channel', row[0], user_id)
			unseen = self.get_unseen(row[0], user_id)
			gold = self.get_channel_gold(row[0])
			channel = {"id": row[0], "name": row[1], "rating": int(row[2]), "rated": rated, "unseen":unseen, "videos":row[3], "username": row[4], "gold": int(gold), "ts":row[5], "nsfw":row[6]}
			channel_list.append(channel)
		return channel_list

	def get_profile(self, profile_id, user_id):
		query = "select user_id, username, first_name, following, followers, gold_received, tokens, score from users where user_id = '%s'" % profile_id
		self.execute(query)
		row = self.cur.fetchone()
		profile = {"id": row[0], "username": row[1], "first_name": row[2], "following": row[3], "followers": row[4], "gold_received": row[5], "tokens": row[6], "score": row[7]}
		query = "select * from follow where follower = '%s' and following = '%s'" % (user_id, profile_id)
		self.execute(query)
		row = self.cur.fetchone()
		if row is None:
			profile["followed"] = 0
		else:
			profile["followed"] = 1
		return profile

	def add_profile(self, android_id, account_id, first_name, last_name, email, username, college):
		query = "select * from users where user_id = '%s'" % account_id
		self.execute(query)
		row = self.cur.fetchone()
		if row is None:
			ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
			first_name = MySQLdb.escape_string(first_name)
			last_name = MySQLdb.escape_string(last_name)
			email = MySQLdb.escape_string(email)
			query = "update users set username = '%s', first_name = '%s', last_name = '%s', email = '%s', user_id = '%s', login = '%s', college = '%s' " \
					"where user_id = '%s'" % (username, first_name, last_name, email, account_id, ts, college, android_id)
			self.execute(query)
			query = "update channels set user_id = '%s' where user_id = '%s'" % (account_id, android_id)
			self.execute(query)
			query = "update comments set user_id = '%s' where user_id = '%s'" % (account_id, android_id)
			self.execute(query)
			query = "update seen set user_id = '%s' where user_id = '%s'" % (account_id, android_id)
			self.execute(query)
			query = "update videos set user_id = '%s' where user_id = '%s'" % (account_id, android_id)
			self.execute(query)
			query = "update votes set user_id = '%s' where user_id = '%s'" % (account_id, android_id)
			self.execute(query)
		else:
			query = "delete from users where user_id = '%s'" % (android_id)
			self.execute(query)

	def follow(self, user_id, following):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into follow (follower, following, ts) values ('%s','%s', '%s')" % (user_id, following, ts)
		self.execute(query)
		query = "update users set following=following+1 where user_id = '%s'" % (user_id)
		self.execute(query)
		query = "update users set followers=followers+1 where user_id = '%s'" % (following)
		self.execute(query)

	def unfollow(self, user_id, following):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "delete from follow where follower = '%s' and following = '%s'" % (user_id, following)
		self.execute(query)
		query = "update users set following=following-1 where user_id = '%s'" % (user_id)
		self.execute(query)
		query = "update users set followers=followers-1 where user_id = '%s'" % (following)
		self.execute(query)


	def giveGold(self, user_id, to, video_id):
		query = "select tokens from users where user_id = '%s'" % user_id
		self.execute(query)
		row = self.cur.fetchone()
		if row[0] > 0:
			ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
			query = "insert into gold (sender, receiver, video_id, ts) values ('%s','%s', '%s', '%s')" % (user_id, to, video_id, ts)
			self.execute(query)
			query = "update users set tokens=tokens-1 where user_id = '%s'" % (user_id)
			self.execute(query)
			query = "update users set gold_received=gold_received+1 where user_id = '%s'" % (to)
			self.execute(query)
			query = "update videos set gold=gold+1 where video_id = '%s'" % (video_id)
			self.execute(query)
			return 1
		else:
			return 0

	def rate_comment(self,comment_id, rating, user_id):
		row_count = self.add_vote(user_id, 'comment', comment_id, rating)
		if row_count != 1: # Previously voted on this
			if rating == "1":
				rating = 2
			elif rating == "-1":
				rating = -2
		self.update_score(comment_id, 2, rating)
		query = "update comments set rating=rating+(%s) where comment_id = '%s'" % (rating,comment_id)
		self.execute(query)

	def rate_channel(self,channel_id, rating, user_id):
		if user_id == adminkey:
			from random import randint
			if rating == "1":
				rating = randint(10,15)
			elif rating == "-1":
				rating = -5
		row_count = self.add_vote(user_id, 'channel', channel_id, rating)
		if row_count != 1 and user_id != adminkey: # Previously voted on this
			if rating == "1":
				rating = 2
			elif rating == "-1":
				rating = -2
		self.update_score(channel_id, 0, rating)
		query = "update channels set rating=rating+(%s) where channel_id = '%s'" % (rating,channel_id)
		self.execute(query)

	def rate_video(self,video_id, rating, user_id):
		if user_id == adminkey:
			from random import randint
			if rating == 1:
				rating = randint(50,100)
			elif rating == -1:
				rating = -5
		row_count = self.add_vote(user_id, 'video', video_id, rating)
		if row_count != 1 and user_id != adminkey: # Previously voted on this
			if rating == 1:
				rating = 2
			elif rating == -1:
				rating = -2
		self.update_score(video_id, 1, rating)

		if user_id == adminkey:
			query = "update videos set boost=boost+(%s) where video_id = '%s'" % (rating,video_id)
		else:
			query = "update videos set rating=rating+(%s) where video_id = '%s'" % (rating,video_id)
		self.execute(query)

	def add_vote(self, user_id, item, item_id, rating):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into votes (user_id, item, item_id, vote, ts) values ('%s','%s', '%s', %s, '%s') ON DUPLICATE KEY UPDATE vote = %s, ts = '%s'" % (user_id, item, item_id, rating, ts, rating, ts)
		if user_id == adminkey:
			query = "insert into votes (user_id, item, item_id, vote, ts) values ('%s','%s', '%s', %s, '%s') ON DUPLICATE KEY UPDATE vote = vote+%s, ts = '%s'" % (user_id, item, item_id, rating, ts, rating, ts)
		self.execute(query)
		return self.cur.rowcount

	def get_rated(self, item, item_id, user_id):
		query = "select vote from votes where item = '%s' and item_id = '%s' and user_id = '%s'" % (item, item_id, user_id)
		self.execute(query)
		vote = self.cur.fetchone()
		if vote is None:
			rated = 0
		else:
			rated = vote[0]
		return rated

	def report_video(self,video_id, user_id):
		query = "update videos set flag=flag+1 where video_id = '%s'" % (video_id)
		self.execute(query)

	def add_seen(self, user_id, video_ids):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		for id in video_ids:
			query = "insert into seen (user_id, video_id, ts) values ('%s','%s', '%s') ON DUPLICATE KEY UPDATE ts = '%s'" % (user_id, id, ts, ts)
			self.execute(query)

	def update_score(self, id, item, points): # no local commit
		if item == 0:
			user_id_query = "select user_id from channels where channel_id = '%s'" % (id)
		elif item == 1:
			user_id_query = "select user_id from videos where video_id = '%s'" % (id)
		elif item == 2:
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

	def get_unseen(self,channel_id, user_id):
		query = "select count(*) from videos V left join (select * from yonderdb.seen where user_id = '%s' ) AS S on V.video_id = S.video_id " \
				"where S.user_id is NULL and channel_id = '%s' and visible = 1 order by rating DESC" % (user_id, channel_id)
		self.execute(query)
		row = self.cur.fetchone()
		return row[0]

	def get_channel_gold(self,channel_id):
		query = "SELECT ifnull(sum(V.gold),0) FROM channels C left join videos V on V.channel_id=C.channel_id where C.channel_id = %s;" % (channel_id)
		self.execute(query)
		row = self.cur.fetchone()
		return row[0]

	def get_hot_score(self, date, rating):
		from math import log
		epoch = datetime(1970, 1, 1)
		td = date - epoch
		epoch_seconds = td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)
		seconds = epoch_seconds - 1134028003
		order = log(max(abs(rating), 1), 10)
		sign = 1 if rating > 0 else -1 if rating < 0 else 0
		return round(sign * order + seconds / 45000, 7)

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

	def update_last_request(self, user_id, version):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into users (user_id, last_request, install_date) values ('%s', '%s', '%s') " \
				"on duplicate key update last_request = values(last_request), visits = visits + 1" % (user_id, ts, ts)
		self.execute(query)
		if self.cur.rowcount == 1:
			from util import Util
			email_body = "User %s" % (user_id)
			# Util.email("New User", email_body)
		query = "update users set version=%s where user_id = '%s'" % (version, user_id)
		self.execute(query)

	def update_last_ping(self, user_id):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into users (user_id, last_ping, install_date) values ('%s', '%s', '%s') on duplicate key update last_ping = values(last_ping)" % (user_id, ts, ts)
		self.execute(query)

	def unlock(self, user_id, code):
		ts = datetime.utcnow()
		query = "update codes set used=used+1 where code = '%s'" % code
		self.execute(query)
		query = "update users set unlocked='%s' where user_id = '%s'" % (ts.strftime("%Y-%m-%d %H:%M:%S"), user_id)
		self.execute(query)
		return 1

		# query = "select expire_ts, used, cap from codes where code = '%s'" % code
		# self.execute(query)
		# row = self.cur.fetchone()
		# if row is None:
		# 	return 0
		# elif row[0] < ts:
		# 	return -1
		# elif row[1] >= row[2]:
		# 	return -2
		# else:
		# 	query = "update codes set used=used+1 where code = '%s'" % code
		# 	self.execute(query)
		# 	query = "update users set unlocked='%s' where user_id = '%s'" % (ts.strftime("%Y-%m-%d %H:%M:%S"), user_id)
		# 	self.execute(query)
		# 	return 1

	def invited(self, user_id, invited_by):
		query = "update users set tokens=tokens+5 where user_id like '%%%s%%'" % (invited_by)
		self.execute(query)

	def join_waitlist(self, user_id, email, college):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "insert into waitlist (email, college, user_id, ts) values ('%s', '%s', '%s', '%s')  on duplicate key update email = '%s', college = '%s', ts = '%s'" % (email, college, user_id, ts, email, college, ts)
		self.execute(query)

	### Notifications

	def get_last_notification_seen_ts(self, user_id, seen):
		query = "select last_notification_seen from users where user_id = '%s'" % user_id
		self.execute(query)
		row = self.cur.fetchone()
		if row is None or row[0] is None:
			ts = '2016-01-01 00:00:00'
		else:
			ts = row[0].strftime("%Y-%m-%d %H:%M:%S")
		if seen == "1":
			now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
			query = "update users set last_notification_seen='%s' where user_id = '%s'" % (now, user_id)
			self.execute(query)
		return ts

	def get_channel_thumbnail(self, channel_id):
		query = "SELECT video_id FROM yonderdb.videos where channel_id = '%s' and visible = 1 order by rating DESC limit 1;" % channel_id
		self.execute(query)
		row = self.cur.fetchone()
		if row is None:
			return ""
		return row[0]

	def get_video_votes(self, user_id, ts):
		video_vote_list = []
		query = "SELECT count(*) as count, caption, video_id FROM votes join videos on video_id = item_id " \
				"where item = 'video' and videos.user_id = '%s' and votes.user_id != '%s' and votes.ts > '%s' group by item_id;" % (user_id, user_id, ts)
		if user_id == adminkey:
			query = "SELECT count(*) as count, caption, video_id FROM votes join videos on video_id = item_id " \
				"where item = 'video' and votes.ts > '%s' group by item_id;" % (ts)
		self.execute(query)
		for row in self.cur.fetchall():
			query = "select channels.name from videos join channels on videos.channel_id = channels.channel_id where video_id = '%s'" % (row[2])
			self.execute(query)
			info = self.cur.fetchone()

			query = "select vote from votes where item_id = '%s' and vote > 0 and user_id = '%s' and ts > '%s'" % (row[2], adminkey, ts)
			self.execute(query)
			extra_people_row = self.cur.fetchone()
			if extra_people_row is None:
				extra_people = 0
			else:
				extra_people =extra_people_row[0]

			video_vote_list.append({"count": row[0] + extra_people, "caption": row[1], "channel": info[0], "video_id":row[2], "thumbnail_id":row[2]})
		return video_vote_list

	def get_comment_votes(self, user_id, ts):
		comment_vote_list = []
		query = "SELECT count(*) as count, comment, video_id FROM votes join comments on comment_id = item_id " \
				"where item = 'comment' and comments.user_id = '%s' and votes.user_id != '%s' and votes.ts > '%s' group by item_id;" % (user_id, user_id, ts)
		if user_id == adminkey:
			query = "SELECT count(*) as count, comment, video_id FROM votes join comments on comment_id = item_id " \
				"where item = 'comment' and votes.ts > '%s' group by item_id;" % (ts)
		self.execute(query)
		for row in self.cur.fetchall():
			query = "select caption, channels.name from videos join channels on videos.channel_id = channels.channel_id where video_id = '%s'" % (row[2])
			self.execute(query)
			info = self.cur.fetchone()
			comment_vote_list.append({"count": row[0], "comment": row[1],"caption": info[0], "channel": info[1], "video_id":row[2], "thumbnail_id": row[2]})

		return comment_vote_list

	def get_channel_votes(self, user_id, ts):
		channel_vote_list = []
		query = "SELECT count(*) as count, name, channel_id FROM votes join channels on channel_id = item_id " \
				"where item = 'channel' and channels.user_id = '%s' and votes.user_id != '%s' and votes.ts > '%s' group by item_id;" % (user_id, user_id, ts)
		if user_id == adminkey:
			query = "SELECT count(*) as count, name, channel_id FROM votes join channels on channel_id = item_id " \
				"where item = 'channel' and votes.ts > '%s' group by item_id;" % (ts)
		self.execute(query)
		for row in self.cur.fetchall():
			channel_vote_list.append({"count": row[0], "name": row[1], "channel_id": row[2], "thumbnail_id": self.get_channel_thumbnail(row[2])})
		return channel_vote_list

	def get_channels_removed(self, user_id, ts):
		list = []
		query = "SELECT name, channel_id FROM channels where channels.user_id = '%s' and visible < 1 and removed_ts > '%s'" % (user_id, ts)
		if user_id == adminkey:
			query = "SELECT name, channel_id FROM channels where visible < 1 and removed_ts > '%s'" % (ts)
		self.execute(query)
		for row in self.cur.fetchall():
			list.append({"name": row[0], "thumbnail_id":self.get_channel_thumbnail(row[1])})
		return list

	def get_videos_removed(self, user_id, ts):
		list = []
		query = "SELECT caption, video_id FROM videos where videos.user_id = '%s' and visible < 1 and removed_ts > '%s'" % (user_id, ts)
		if user_id == adminkey:
			query = "SELECT caption, video_id FROM videos where visible < 1 and removed_ts > '%s'" % (ts)
		self.execute(query)
		for row in self.cur.fetchall():
			list.append({"name": row[0], "thumbnail_id": row[1]})
		return list

	def get_comments_removed(self, user_id, ts):
		list = []
		query = "SELECT comment, video_id FROM comments where comments.user_id = '%s' and visible < 1 and removed_ts > '%s'" % (user_id, ts)
		if user_id == adminkey:
			query = "SELECT comment, video_id FROM comments where visible < 1 and removed_ts > '%s'" % (ts)
		self.execute(query)
		for row in self.cur.fetchall():
			list.append({"name": row[0], "thumbnail_id": row[1]})
		return list

	def get_new_channel_videos(self, user_id, ts):
		notification_list = []
		query = "SELECT count(*), C.name, C.channel_id FROM videos V join channels C on V.channel_id = C.channel_id " \
				"where C.user_id = '%s' and V.user_id != '%s' and V.ts > '%s' and V.visible = 1 and C.visible = 1 " \
				"group by C.channel_id;" % (user_id, user_id, ts)
		if user_id == adminkey:
			query = "SELECT count(*), C.name, C.channel_id FROM videos V join channels C on V.channel_id = C.channel_id " \
				"where V.user_id != '%s' and V.ts > '%s' and V.visible = 1 and C.visible = 1 " \
				"group by C.channel_id;" % (user_id, ts)
		self.execute(query)
		for row in self.cur.fetchall():
			notification_list.append({"count": row[0], "name": row[1], "channel_id": row[2], "thumbnail_id": self.get_channel_thumbnail(row[2])})
		return notification_list

	def get_new_video_comments(self, user_id, ts):
		notification_list = []
		query = "SELECT count(*), V.caption, V.video_id FROM videos V join comments C on V.video_id= C.video_id " \
				"where C.user_id != '%s' and V.user_id = '%s' and C.ts > '%s' and V.visible = 1 and C.visible = 1 " \
				"group by V.video_id;" % (user_id, user_id, ts)
		if user_id == adminkey:
			query = "SELECT count(*), V.caption, V.video_id FROM videos V join comments C on V.video_id= C.video_id " \
				"where C.user_id != '%s' and C.ts > '%s' and V.visible = 1 and C.visible = 1 " \
				"group by V.video_id;" % (user_id, ts)
		self.execute(query)
		for row in self.cur.fetchall():
			notification_list.append({"count": row[0], "name": row[1], "video_id":row[2], "thumbnail_id": row[2]})
		return notification_list

	def get_other_video_replies(self, user_id, ts):
		notification_list = []
		oldest = datetime.utcnow() - timedelta(hours = 24)
		follow_ts = oldest.strftime("%Y-%m-%d %H:%M:%S")
		# join videos with channels where you recently uploaded video
		query = "SELECT count(*), C.name, C.channel_id FROM videos V join " \
				"(SELECT C.channel_id, C.name, C.user_id, C.visible FROM videos V join channels C on V.channel_id = C.channel_id " \
				"where V.user_id = '%s' and C.user_id != '%s' and V.ts > '%s' and V.visible = 1 and C.visible = 1  group by C.channel_id) C on V.channel_id = C.channel_id " \
				"join (select max(ts) as last_reply_ts, channel_id from videos where user_id = '%s' group by channel_id) M on V.channel_id = M.channel_id " \
				"where C.user_id != '%s' and V.user_id != '%s' and V.ts > '%s' and V.ts > M.last_reply_ts and V.visible = 1 and C.visible = 1 " \
				"group by C.channel_id;" % (user_id, user_id, follow_ts,user_id, user_id, user_id, ts)
		self.execute(query)
		for row in self.cur.fetchall():
			notification_list.append({"count": row[0], "name": row[1], "channel_id":row[2], "thumbnail_id":self.get_channel_thumbnail(row[2])})
		return notification_list

	def get_other_comment_replies(self, user_id, ts):
		notification_list = []
		oldest = datetime.utcnow() - timedelta(hours = 24)
		follow_ts = oldest.strftime("%Y-%m-%d %H:%M:%S")
		# join comments with videos where you recently uploaded video
		query = "SELECT count(*), V.caption, V.video_id FROM comments C join " \
				"(SELECT V.video_id, V.caption, V.user_id, V.visible FROM videos V join comments C on V.video_id= C.video_id " \
				"where C.user_id = '%s' and V.user_id != '%s' and C.ts > '%s' and V.visible = 1 and C.visible = 1  group by V.video_id) V on V.video_id= C.video_id " \
				"join (select max(ts) as last_reply_ts, video_id from comments where user_id = '%s' group by video_id) M on V.video_id = M.video_id " \
				"where C.user_id != '%s' and V.user_id != '%s' and C.ts > '%s' and C.ts > M.last_reply_ts and V.visible = 1 and C.visible = 1 " \
				"group by V.video_id" % (user_id, user_id, follow_ts, user_id, user_id, user_id, ts)
		self.execute(query)
		for row in self.cur.fetchall():
			notification_list.append({"count": row[0], "name": row[1], "video_id":row[2], "thumbnail_id": row[2]})
		return notification_list


	def get_gold_received(self, user_id, ts):
		gold_received_list = []
		query = "SELECT count(*) as count, G.video_id, V.caption FROM gold G join videos V on G.video_id = V.video_id " \
				"where receiver = '%s' and G.ts > '%s' group by G.video_id;" % (user_id, ts)
		if user_id == adminkey:
			query = "SELECT count(*) as count, G.video_id, V.caption FROM gold G join videos V on G.video_id = V.video_id " \
				"where G.ts > '%s' group by G.video_id;" % (ts)
		self.execute(query)
		for row in self.cur.fetchall():
			query = "select channels.name from videos join channels on videos.channel_id = channels.channel_id where video_id = '%s'" % (row[1])
			self.execute(query)
			info = self.cur.fetchone()
			gold_received_list.append({"count": row[0], "video_id" :row[1] , "caption": row[2], "channel": info[0], "thumbnail_id": row[1]})
		return gold_received_list

	def get_followers(self, user_id, ts):
		query = "SELECT count(*) as count FROM follow where following = '%s' and ts > '%s';" % (user_id, ts)
		self.execute(query)
		row = self.cur.fetchone()
		return row[0]

	### Cron

	def cleanup(self): # missing gold
		oldest = datetime.utcnow() - timedelta(hours = 72)
		ts = oldest.strftime("%Y-%m-%d %H:%M:%S")

		query = "select video_id from videos V where V.removed_ts < '%s' and visible < 1" % ts
		self.execute(query)
		ids = []
		for row in self.cur.fetchall():
			ids.append(row[0])

		query = "select video_id from videos V join channels C on V.channel_id = C.channel_id where C.removed_ts < '%s' and C.visible < 1" % ts
		self.execute(query)
		for row in self.cur.fetchall():
			ids.append(row[0])
		query = "Delete V FROM channels C join votes V on V.item_id = C.channel_id where C.removed_ts < '%s' and C.visible < 1" % ts
		self.execute(query)
		query = "Delete C from channels C where C.removed_ts < '%s' and C.visible < 1" % ts
		self.execute(query)

		if len(ids) > 0: # if you are deleting videos cause video or channel is invisible
			query = "Delete C FROM videos V join comments C on V.video_id = C.video_id where V.removed_ts < '%s' and V.visible < 1" % ts
			self.execute(query)
			query = "Delete S FROM videos V join seen S on V.video_id = S.video_id where V.removed_ts < '%s' and V.visible < 1" % ts
			self.execute(query)
			query = "Delete T FROM videos V join votes T on V.video_id = T.item_id where V.removed_ts < '%s' and V.visible < 1" % ts
			self.execute(query)
			query = "Delete V from videos V where V.removed_ts < '%s' and V.visible < 1" % ts
			self.execute(query)

		query = "Delete V FROM comments C join votes V on C.comment_id = V.item_id where C.removed_ts < '%s' and C.visible < 1" % ts
		self.execute(query)
		query = "Delete C from comments C where C.removed_ts < '%s' and C.visible < 1" % ts
		self.execute(query)

		return ids

	def cron_set_invisible(self):
		ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
		query = "update videos set visible=-1, removed_ts = '%s' where rating + boost < -4 and visible = 1" % (ts)
		self.execute(query)

		# query = "update videos set removed_ts = '%s' where visible = 0 and removed_ts is null" % ts ##### CHANGE ME
		# self.execute(query)

		# query = "update comments set visible=-1, removed_ts = '%s' where rating < -4 and visible = 1" % ts
		# self.execute(query)
		query = "update channels set visible=-1, removed_ts = '%s' where rating < -10 and visible = 1 and user_id != '%s'" % (ts, adminkey)
		self.execute(query)

		query = "update channels C left join (select count(video_id) as count, sum(IFNULL(rating, 0)) as rating, channel_id from videos where visible = 1 and rating + boost > -2 group by channel_id) V " \
				"on C.channel_id = V.channel_id set C.visible = -1 " \
				"where TIMESTAMPDIFF(MINUTE, C.ts, now()) >= 15 and C.visible = 1 and IFNULL(V.count,0) = 0;"
		self.execute(query)

		query = "update channels set visible=-2 where TIMESTAMPDIFF(HOUR, ts, now()) >= 24 and visible = 1 and user_id != '%s'" % adminkey
		self.execute(query)
		query = "update videos set visible=-2 where TIMESTAMPDIFF(HOUR, ts, now()) >= 24 and visible = 1 and user_id != '%s'" % adminkey
		self.execute(query)

	def fake_rating(self):
		query = "select video_id from videos where boost = 0 and user_id = '%s'" % adminkey
		self.execute(query)
		from random import randint
		for row in self.cur.fetchall():
			points = randint(10,30)
			query = "update videos set boost = boost +(%s) where video_id = '%s'" % (points, row[0])
			self.execute(query)
			self.update_score(row[0], True, points) #old

	def set_hot_score(self):
		query = "select C.channel_id, sum(IFNULL(V.rating, 0)) + C.rating as rating, C.ts from channels C left join videos V on C.channel_id = V.channel_id and V.visible = 1 and V.rating >= 0 " \
					"where C.visible = 1 group by C.channel_id"
		self.execute(query)
		for row in self.cur.fetchall():
			hot_score = self.get_hot_score(row[2], row[1])
			query = "update channels set hot_score = %s where channel_id = '%s'" % (hot_score, row[0])
			self.execute(query)




















