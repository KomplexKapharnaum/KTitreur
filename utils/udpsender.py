#!/usr/bin/env python

import time
import socket

IP = '2.0.255.255'
PORT = 3742

with open('scenario.txt') as f:
    content = f.readlines()

# you may also want to remove whitespace characters like `\n` at the end of each line
content = [x.strip() for x in content]

for line in content:
	if line.startswith('#'):
		data = line.split(' ')

		if data[0] == "#ip":
			if len(data) > 1:
				IP = data[1]
		elif data[0] == "#port":
			if len(data) > 1:
				PORT = int(data[1])
		elif data[0] == "#wait":
			if len(data) > 1:
				time.sleep(int(data[1])/1000.0)

	elif line != '':
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if IP.endswith('255'):
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.sendto(line, (IP, PORT))
		time.sleep(0.1)
		print ('sent', line)
