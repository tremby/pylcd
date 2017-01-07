# pylcd

NAME = "pylcd"
VERSION = "0.1~git"
DESCRIPTION = "Python library to interface with LCDd"
AUTHOR = "Bart Nagel"
AUTHOR_EMAIL = "bart@tremby.net"
URL = "TODO"
LICENSE = "GPLv3"

import socket

class Pylcd:
	_width = None
	_height = None
	_cellwidth = None
	_cellheight = None
	_s = None
	_verbose = False

	_screens = {}

	def getsuccess(self):
		"""Get data from LCDd until a success or error message is received
		"""
		if not self.connected(): raise Exception("not connected")
		while True:
			response = self._s.recv(1024).strip().split("\n")
			successorfail = False
			for line in response:
				if self._verbose: print "Message from LCDd: \"%s\"" % line
				if line == "success" or line[0:4] == "huh?":
					successorfail = True
					break
			if successorfail:
				return line == "success"
			# else recieve data again

	def getwidth(self):
		"""Get the width in cells of the LCD"""
		if not self.connected(): raise Exception("not connected")
		return self._width
	def getheight(self):
		"""Get the height in cells of the LCD"""
		if not self.connected(): raise Exception("not connected")
		return self._height
	def getcellwidth(self):
		"""Get the width in pixels of one cell of the LCD"""
		if not self.connected(): raise Exception("not connected")
		return self._cellwidth
	def getcellheight(self):
		"""Get the height in pixels of one cell of the LCD"""
		if not self.connected(): raise Exception("not connected")
		return self._cellheight
	def getscreens(self):
		"""Get an array of screen names owned by this client"""
		if not self.connected(): raise Exception("not connected")
		return self._screens
	def getwidgets(self, screen):
		"""Get the set of widget names owned by a particular screen of this 
		client"""
		if not self.connected(): raise Exception("not connected")
		try:
			return self._screens[screen]
		except KeyError:
			raise ValueError("screen '%s' doesn't exist" % screen)

	def send(self, message, getresponse=True):
		"""Send a raw command to LCDd
		A newline character is appended.
		If getresponse is True, wait for a success or error response and return 
		a boolean. Otherwise (if getresponse is False) the getsuccess method can 
		be used.
		"""
		self._s.send("%s\n" % message)
		if getresponse:
			return self.getsuccess()

	def printline(self, screen, line, text, name, usewidth = None, offset = 0, frame = None):
		"""Print a string to a particular line of the display
		Use string or scroller based on text length
		"""
		if offset >= self.getwidth():
			raise ValueError("offset too big")

		if usewidth is None:
			if offset > 0:
				usewidth = self.getwidth() - offset
			else:
				usewidth = self.getwidth()

		if name in self.getwidgets(screen):
			if self._verbose: print "Widget '%s' already exists on screen '%s', removing it" % (name, screen)
			if not self.send("widget_del %s %s" % (screen, name)):
				if self._verbose: print "It didn't exist after all -- weird but no problem"
		if frame:
			fr = " -in %s" % frame
		if len(text) <= usewidth:
			if self._verbose: print "Adding string widget %s" % name
			fr = ""
			self.send("widget_add %s %s string%s" % (screen, name, fr), False)
		else:
			if self._verbose: print "Adding scroller widget %s" % name
			self.send("widget_add %s %s scroller%s" % (screen, name, fr), False)
		if self.getsuccess():
			self._widgets.append(name)
		else:
			raise Exception("Could not add widget")
		if len(text) <= usewidth:
			screenoffset = offset + round((usewidth - len(text)) / 2)
			if self._verbose: print "Printing \"%s\" to string widget with screenoffset %d" % (text, screenoffset)
			self.send("widget_set %s %s %d %d \"%s\"" % (screen, name, screenoffset + 1, line, text.replace('"', '\\"')), False)
		else:
			if self._verbose: print "Printing \"%s\" to scroller widget" % text
			self.send("widget_set %s %s %d %d %d %d h 1 \"%s\"" % (screen, name, offset + 1, line, offset + usewidth, line, text.replace('"', '\\"')), False)
		if not self.getsuccess():
			raise Exception("Could not set widget text")

	def connect(self, clientname, host="localhost", port=13666):
		"""Open the socket to LCDd and do the handshake
		"""
		if self.connected(): raise Exception("already connected")
		if self._verbose: print "Connecting to LCDd on %s port %d" % (host, port)
		self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._s.connect((host, port))
		if not self._s:
			raise Exception("Could not connect to LCDd")

		# say hello and get display dimensions
		if self._verbose: print "Getting display dimension information"
		self.send("hello", False)
		response = self._s.recv(1024).split()
		while len(response):
			atom = response.pop(0)
			if atom == "wid":
				self._width = int(response.pop(0))
				if self._verbose: print "Display is %d cells wide" % self.getwidth()
			elif atom == "hgt":
				self._height = int(response.pop(0))
				if self._verbose: print "Display is %d cells high" % self.getheight()
			elif atom == "cellwid":
				self._cellwidth = int(response.pop(0))
				if self._verbose: print "Cells are %d pixels wide" % self.getcellwidth()
			elif atom == "cellhgt":
				self._cellheight = int(response.pop(0))
				if self._verbose: print "Cells are %d pixels high" % self.getcellheight()

		# identify ourselves
		if self._verbose: print "Identifying ourselves to LCDd"
		if not self.send("client_set -name %s" % clientname):
			raise Exception("Could not set client name")

	# TODO: disconnect method

	def addscreen(self, name, priority="hidden"):
		"""Add a screen with the given name
		"""
		if self._verbose: print "Adding a new screen with name %s" % name
		if not self.send("screen_add %s" % name):
			raise Exception("Could not add screen")
		self._screens[name] = set()
		self.priority(name, priority)

	def heartbeat(self, on):
		"""Switch the heartbeat on or off
		"""
		if self._verbose: print "Switching the heartbeat on or off"
		val = "off"
		if on: val = "on"
		if not self.send("screen_set screen -heartbeat %s" % val):
			raise Exception("Could not switch off heartbeat")

	def priority(self, screen, priority):
		if priority not in self.PRIORITY:
			raise ValueError("invalid priority class '%s'" % priority)

		if self._verbose: print "Setting screen to priority \"%s\"" % priority

		if not self.send("screen_set %s -priority %s" % (screen, priority)):
			raise Exception("Could not set priority")

	def connected(self):
		"""Return True if connected to LCDd"""
		return bool(self._s)

	PRIORITY = [
			"hidden",
			"background",
			"info",
			"foreground",
			"alert",
			"input",
			]
