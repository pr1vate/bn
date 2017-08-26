#!/usr/bin/env python2

#
# GrayAnt - IRC Logging Framework
#

from Queue import Queue
from threading import Thread

import argparse
import socket
import select
import string
import random
import ssl
import sys
import re

BUFFER = 512


#
# Class Creation
#
class GrayAnt(object):
    def __init__(self, host, port, user, nick, nickpass, channel, ssl_flag):
        self.readQueue = Queue(maxsize=0)
        self.writeQueue = Queue(maxsize=0)
        self.host = self.__get_host(host)
        self.port = port
        self.user = user
        self.nick = nick
        self.channel = channel
        self.nickpass = nickpass
        self.ssl_flag = ssl_flag
        self.connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if ssl_flag is True or port == '6697': self.sock = ssl.wrap_socket(self.sock)
        # Start the process internally (may look at external start for threading purposes.. #todoo
        self.__connect()

    def data_handler(self):
        while True:
            readable, writable, errs = select.select([self.sock],[self.sock],[],1)
            if self.sock in readable:
                data = self.sock.recv(BUFFER)
                if data: self.readQueue.put(data)
                self.__msg_parser()

            if self.sock in writable:
                if self.writeQueue.empty() is not True:
                    self.sock.send(self.writeQueue.get())
                    self.writeQueue.task_done()

    def __msg_parser(self):
        if self.readQueue.empty() is not True:
            data = self.readQueue.get()
            if '\r\n' in data:
                lines = data.split('\r\n')
                for x in xrange(len(lines)):
                    if lines[x]:
                        regex = '^(:(\S+) )?(\S+)( (?!:)(.+?))?( :(.+))?$'
                        m = re.match(regex, lines[x], re.M | re.I)
                        if not m:
                            return


                        #print 'M : ', m.group()
                        #print 'M1: ', m.group(1)
                        #print 'M2: ', m.group(2)
                        #print 'M3: ', m.group(3)
                        #print 'M4: ', m.group(4)
                        #print 'M5: ', m.group(5)
                        #print 'M6: ', m.group(6)

                        msg_full = m.group()
                        msg_prefix = m.group(2)
                        msg_command = m.group(3)
                        msg_params = m.group(5)
                        msg_trailing = m.group(6)

                        print msg_full
                        print 'Prefix:   %s' % (msg_prefix)
                        print 'Command:  %s' % (msg_command)
                        print 'Param:    %s' % (msg_params)
                        print 'Trailing: %s' % (msg_trailing)

                        if msg_command.lower() == 'ping':
                            self.writeQueue.put("PONG %s\r\n" % (msg_trailing).lstrip(' '))
                            #print "[--->] PONG %s" % (msg_trailing).lstrip(' ')

                        if msg_command == '002':
                            self.connected = True

                        if msg_command == '396':
                            self.writeQueue.put("JOIN %s\r\n" % (self.channel))

                        if msg_command == '432':
                            self.writeQueue.put("NICK %s\r\n" % (self.user))

                        if msg_command.lower() == 'notice' and self.connected == False:
                            #different ways to handle NOTICE messages
                            if 'found your hostname' in msg_trailing.lower():
                                #self.writeQueue.put("PASS *\r\n")
                                self.writeQueue.put("NICK %s\r\n" % (self.nick))
                                self.writeQueue.put("USER %s %d %d :%s\r\n" % (self.user, 8, 0, "yeh, im that nigga!"))

                        if msg_command.lower() == 'privmsg':
                            if msg_params.lower() == self.channel:
                                if msg_trailing.lstrip(' :') == 'help me':
                                    print ":%s PRIVMSG %s :I can see you... INFORMATION BLAH BLAH..\r\n" % (msg_prefix, msg_params)
                                    self.writeQueue.put(":%s PRIVMSG %s :I can see you... INFORMATION BLAH BLAH..\r\n" % (msg_prefix, msg_params))
                                else:
                                    print msg_trailing

            self.readQueue.task_done()



    def __connect(self):
        try:
            self.sock.connect((self.host, int(self.port)))
            self.sock.setblocking(1)
        except socket.error as e:
            self.__error("[>] Socket Error: '%s' says '%s'\n" % (self.host, e.args[1]))

    def __get_host(self, host):
        try:
            return socket.gethostbyname(host)
        except socket.gaierror as g:
            self.__error("[>] Socket Error: '\033[1m%s\033[0m' says '\033[1m%s\033[0m'\n" % (host, g.args[1]))

    def __error(self, msg):
        if not msg: sys.exit(1)
        print "\n%s\n" % (msg)
        sys.exit(1)

#
# Main
#
def Usage():
    print "\n\033[1mUSAGE\033[0m:"
    print "  %s -h irc.blackcatz.org -p 6697" % (sys.argv[0])
    print "  %s -h irc.blackcatz.org -p 6697 -u user" % (sys.argv[0])
    print "  %s -h irc.blackcatz.org -p 6697 -u user -n nick" % (sys.argv[0])
    print "  %s -h irc.blackcatz.org -p 6697 -u user -n nick -P *password* -s" % (sys.argv[0])
    print "  %s -h irc.blackcatz.org -p 6697 -u user -n nick -P *password* -c '#howtohack'-s" % (sys.argv[0])
    print "\n\033[1mOPTIONS\033[0m:"
    print "  '-h', '--host'     - The IRC Server host we want to use"
    print "  '-p', '--port'     - The IRC Server service port number"
    print "  '-u', '--user'     - Set a custom username for IRC connection"
    print "  '-n', '--nick'     - Set a custom nick for the IRC connection"
    print "  '-P', '--nickpass' - Set a custom nick password for the IRC nick registration"
    print "  '-c', '--channel'  - Set a custom nick for the IRC connection"
    print "  '-s', '--ssl'      - Boolean flag to force SSL-Enabled Connection"

def RandomString(len=5):
    return 'm'.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(len))

def Error(msg):
    if not msg: return
    print "\n\033[1m%s\033[0m\n" % (msg)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False, usage=Usage)
    parser.add_argument('-h', '--host', action='store', dest='host', default='')
    parser.add_argument('-p', '--port', action='store', dest='port', default='6667')
    parser.add_argument('-u', '--user', action='store', dest='user', default='')
    parser.add_argument('-n', '--nick', action='store', dest='nick', default='')
    parser.add_argument('-P', '--nickpass', action='store', dest='nickpass', default='')
    parser.add_argument('-c', '--channel', action='store', dest='channel', default='#bawts')
    parser.add_argument('-s', '--ssl', action='store_true', dest='ssl_flag', default=False)

    try:
        args = parser.parse_args()
    except TypeError as e:
        Error("The options you provided were not supplied correctly. Please take another look at the examples.")
        Usage()
        sys.exit(1)

    if not args.host or not args.port:
        Usage()
        sys.exit(1)
    if not args.user: args.user = RandomString(4)
    if not args.nick: args.nick = RandomString(4)

    Minion = GrayAnt(args.host, args.port, args.user, args.nick, args.nickpass, args.channel, args.ssl_flag)
    Minion.data_handler()