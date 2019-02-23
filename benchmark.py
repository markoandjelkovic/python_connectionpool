#!/usr/bin/python

import time
import httplib
from connectionpool import HTTPConnectionPool

# 0
#conn = httplib.HTTPConnection("localhost", 80)
# 1
pool = HTTPConnectionPool()
# 2
host = pool.get("localhost", 80)

counter = 0
was = time.time()
average_speed = 0
average_count = 0
while True:
#   1
#	conn = httplib.HTTPConnection("localhost", 80)
#	conn.request("GET", "/wsgi-test", "", {"Connection": "keep-alive"})
#	resp = conn.getresponse()
#	resp.read()
#   2
#	resp = pool.request("localhost", 80, "GET", "/wsgi-test", headers={"Connection": "keep-alive"})
#	resp.read()
#   3
	resp = host.request("GET", "/wsgi-test", headers={"Connection": "keep-alive"})
	resp.read()
	counter += 1
	if counter > 300:
		now = time.time()
		speed = counter/(now - was)
		print "Speed is {0} request/sec".format(speed)
		was = now
		counter = 0
		average_speed += speed
		average_count += 1
	if average_count > 10:
		print "--"
		print "Average speed is {0}".format(average_speed/average_count)
		average_speed = 0
		average_count = 0
