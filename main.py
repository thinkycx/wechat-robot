#!/usr/bin/python
#coding=utf-8
"""
date: 20190203
Usage:
	demo use for wxpy api
"""

import time
from wxpy import *


class Wechat():
	"""
	微信类，封装了一些常用的需求
	"""
	__bot = ''            # Bot()
	__not_friends = []      # item: (remark_name，nickname)
	__reply_once = []

	def __init__(self, console_qr=True, cache=True,  autoreply=0):
		self.__bot = Bot(console_qr=console_qr, cache_path=cache)  # cache_path 保存session信息到wxpy.pkl文件

		# 自动接收响应好友请求，似乎不起作用
		@self.__bot.register(msg_types=FRIENDS)
		def new_friend(msg):
			if msg.card in '':
				return
			user = msg.card.accept()
			user.send("Hello")

		if autoreply:
			# 自动回复朋友的信息一次
			@self.__bot.register(chats=Friend, except_self=True)
			def auto_reply_friends(msg):
				print(msg.chat.name + u'发来消息：' + msg.text)
				if msg.chat.name == 'somebody':
					return u'{0}, 定制消息。\n > {1}'.format(msg.chat.name, msg.text)
				if msg.chat.name not in self.__reply_once:
					self.__reply_once.append(msg.chat.name)
					return u'2019猪事顺利！'
			# return u'{0}，你好！你发送的信息已经收到\n > {1}'.format(msg.chat.name, msg.text)

			# 自动回复群聊消息
			@self.__bot.register(chats=Group, except_self=True)
			def auto_reply_groups(msg):
				# 如果是群聊，但没有被 @，则不回复
				if isinstance(msg.chat, Group) and not msg.is_at:
					return
				return u'新春快乐，祝身体健康，万事如意。'

	def get_bot(self):
		"""
		返回wxpy的Bot对象，用于测试api
		:return:
		"""
		return self.__bot

	def send_image(self, friend, filename):
		"""
		发送指定图片给指定好友.
		如果发送失败，存储(remark_name，nickname)到__not_friends中。如果发送成功，返回0。
		:param friend:
		:param filename:
		:return:
		"""
		try:
			friend.send_image(filename)
		except exceptions.ResponseError as e:
			info = (friend.remark_name, friend.nick_name)
			self.__not_friends.append(info)
			logging.info("Send failed to [ " + info[0] + " " +info[1] + '] ' + str(e))
			return -1
		return 0

	def sendall_image(self, filename='./QR.jpg', nap=0.5, debug=0):
		"""
		发送指定图片给所有好友。
		:param filename: 图片相对路径
		:param nap: 两次发送的时间间隔
		:param debug: 单独发送给一个人测试一下
		:return:
		"""
		if debug:
			friends = self.__bot.search('sun')
			friend = friends[0]
			self.send_image(friend, filename)

		else:
			yes = raw_input(u'确定发送图片给所有好友？')
			if yes != 'y':
				return -1
			friends = self.__bot.friends()
			for i in friends:
				self.send_image(i, filename)
				time.sleep(nap)

	def send_to_file_helpder(self):
		"""
		发送检测出来的非好友信息给文件传输助手。
		:return:
		"""
		info = u"您一共 %d 个好友，检测出%d 个好友已经把您删除。\n" % (len(self.__bot.friends()), len(self.__not_friends))
		for i in self.__not_friends:
			info += u"微信昵称：%s 备注： %s \n" % (unicode(i[0]), unicode(i[1]))
		self.__bot.file_helper.send(info)

	def send_text_to_friend(self, name, message, times=1, nap=0.5, debug=0):
		"""
		发送消息给指定的人。
		:param name: 要发送的人，模糊匹配，可以搜索nickname或者是备注
		:param message: 消息内容
		:param times: 发送次数
		:param nap: 两次发送的间隔时长
		:param debug: 是否需要显示发送多少次
		:return:
		"""
		friends = self.__bot.search(name)
		if not friends:
			logging.info("cannot find %s" % name)
			return -1
		friend = friends[0]
		for i in range(times):
			if debug:
				friend.send(message + u" 第 %d 次" % (i+1) )
			else:
				friend.send(message)
			time.sleep(nap)

	def send_text_to_all_friends(self, message, snap=3):
		"""
		群发短信
		:param message: 信息内容
		:param snap: 两条消息之间的间隔时间
		:return:
		"""
		friends = self.__bot.friends()
		for i in friends:
			try:
				i.send(message)
			except Exception as e:
				print(i), e ,"发送失败"
			time.sleep(snap)

	def scheduled_send(self, name, message, sendtime="2019-02-09 15:55:00"):
		"""
		定时发送消息给好友。
		:param name: 好友备注
		:param message: 消息内容
		:param sendtime: 指定发送的时间
		:return:
		"""
		# 转换成时间数组
		timeArray = time.strptime(sendtime, "%Y-%m-%d %H:%M:%S")
		# 转换成时间戳
		timestamp = time.mktime(timeArray)
		while True:
			if int(time.time()) >= timestamp:
				self.send_text_to_friend(name, message)
				logging.info("send success!")
				return
			time.sleep(10)


def set_log():
	# 设置log
	log_format = "%(asctime)s - %(levelname)s - %(message)s"
	date_format = "%m/%d/%Y %H:%M:%S %p"
	logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)


def detect_deleted_friends():
	# 检测对方是否把你删除：发送消息给每一个人，以此来检测谁把你删除了。
	wechat = Wechat()

	wechat.sendall_image(debug=1)
	wechat.send_to_file_helpder()


if __name__ == '__main__':
	set_log()

	# 登陆
	wechat = Wechat()
	# wechat = Wechat(autoreply=1)

	# 发送信息给所有好友
	# wechat.send_text_to_all_friends(message=u"""春节快乐""")

	# 定时发送
	# wechat.scheduled_send("sun", "hello!", sendtime="2019-02-09 15:56:40")

	# 发送指定次数的消息给好友
	# wechat.send_text_to_friend(u'haha', u'haha最帅', times=10, debug=1)

	# 方便terminal调试api
	wx = wechat.get_bot()
	embed()