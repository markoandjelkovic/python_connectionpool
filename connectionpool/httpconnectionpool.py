# This module is part of python-connectionpool and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php


import httplib
import socket

from .connectionpool import (
	ConnectionPool,
	ConnectionWrapper,
	PoolBrokenConnectionError,
	SingleHostConnectionPool,
)


#FIXME: more strong connection status check
class _HTTPConnectionWrapper(ConnectionWrapper):

	def ok(self):
		return (self.conn.sock is not None)

	def close(self):
		self.conn.close()

	def request(self, *args, **kwargs):
		self.conn.request(*args, **kwargs)
		return self.conn.getresponse()


def _create_connection(host, port=None, strict=False, conn_timeout=None, net_timeout=None):
	"""Create new connection"""

	conn = httplib.HTTPConnection(host=host, port=port, strict=strict, timeout=conn_timeout)
	conn.connect()
	conn.timeout = net_timeout
	conn.sock.settimeout(conn.timeout)

	return _HTTPConnectionWrapper(conn)


def _send_request(conn, method, url, body=None, headers={}):
		try:
			return conn.request(method, url, body=body, headers=headers)
		except socket.timeout as e:
			raise e
		except (httplib.HTTPException, socket.error) as e:
			raise PoolBrokenConnectionError(e)


class HTTPSingleHostConnectionPool(SingleHostConnectionPool):
	def request(self, method, url, body=None, headers={}):
		return SingleHostConnectionPool.request(
			self, lambda conn: _send_request(conn, method, url, body=body, headers=headers))


class HTTPConnectionPool(ConnectionPool):

	SingleHostPoolCls = HTTPSingleHostConnectionPool

	def __init__(
		self, strict=False, conn_timeout=None, net_timeout=None,
		cache_size=100, pool_size=100, pool_block=False, pool_timeout=None):

		ConnectionPool.__init__(
			self,
			lambda host, port: _create_connection(host, port, strict, conn_timeout, net_timeout),
			cache_size=cache_size,
			pool_size=pool_size, pool_block=pool_block, pool_timeout=pool_timeout)

	def request(self, host, port, method, url, body=None, headers={}):
		return self.get(host, port).request(method, url, body=body, headers=headers)

