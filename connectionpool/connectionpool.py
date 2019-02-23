# Simple Connection pool framework based on idea derived from
# urllib3 library (https://github.com/shazow/urllib3)
#
# This module is part of python-connectionpool and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php


import logging
import socket
import httplib
import Queue

from .lrucache import LRUCache


class PoolIsEmptyError(Exception):
	"""Notifies clients that underlying pool is empty"""

	def __init__(self):
		Exception.__init__(self, "Pool reached maximum size and no more connections are allowed.")


class PoolIsClosedError(Exception):
	"""Notifies clients that underlying pool is closed"""

	def __init__(self):
		Exception.__init__(self, "Pool is closed.")


class PoolBrokenConnectionError(Exception):
	"""Request pool manager to recreate connection"""

	def __init__(self, expt):
		self.expt = expt
		Exception.__init__(self, "Broken connection.")


class ConnectionWrapper:
	"""Base class for connection wrapper"""

	def __init__(self, conn):
		self.conn = conn

	def ok(self):
		"""Validate whether connection is open"""

		return True

	def close(self):
		"""Close connection"""

		pass


class SingleHostConnectionPool:
	"""Connection pool for one target location"""

	def __init__(self, connection_factory,
		pool_size=1, pool_block=False, pool_timeout=None):

		self.__connection_factory = connection_factory

		self.__pool_size = pool_size
		self.__pool_block = pool_block
		self.__pool_timeout = pool_timeout
		self.__pool = Queue.LifoQueue(self.__pool_size)

		# Fill the queue up so that doing get() on it will block properly
		for _ in xrange(pool_size):
			self.__pool.put(None)

	def get_pool_size(self):
		"""Returns maximum possible pool size"""

		return self.__pool_size

	def _get_conn(self):
		"""Obtain an existing connection or create a new one"""

		conn = None
		try:
			conn = self.__pool.get(block=self.__pool_block, timeout=self.__pool_timeout)
			if conn and not conn.ok():
				conn.close()
				conn = None
		except AttributeError as e: # self.__pool is None
			raise PoolIsClosedError()
		except Queue.Empty:
			raise PoolIsEmptyError()

		return conn or self.__connection_factory()

	def _put_conn(self, conn):
		"""Return connection back to pool"""

		try:
			self.__pool.put(conn)
		except Exception as e:
			conn.close()

	def close(self):
		"""Close connection pool"""

		oldpool, self.__pool = self.__pool, None
		try:
			while True:
				conn = oldpool.get(block=False)
				if conn:
					conn.close()
		except Queue.Empty:
			pass

	def request(self, callback):
		"""Get HTTP request from pool and pass it to callback"""

		retries = 2
		while retries > 0:
			retries -= 1
			conn = self._get_conn()
			try:
				return callback(conn)
			except PoolBrokenConnectionError as e:
				# Possible problems with pooled connections, give a second chance
				conn.close()
				conn = None
				if retries == 0:
					raise e.expt
			finally:
				self._put_conn(conn)


class ConnectionPool:
	"""Connection pool for arbitrary target locations"""

	SingleHostPoolCls = SingleHostConnectionPool

	def __init__(
		self, connection_factory,
		cache_size=100, pool_size=1, pool_block=False, pool_timeout=None):

		self.__cache_size = cache_size
		self.__cache = LRUCache(cache_size=self.__cache_size, disposefunc=lambda p: p.close())
		self.__connection_factory = connection_factory

		self.__pool_size = pool_size
		self.__pool_block = pool_block
		self.__pool_timeout = pool_timeout

	def get_cache_max_size(self):
		"""Return maximum possible size of LRU cache"""

		return self.__cache_size

	def get_cache_cur_size(self):
		"""Return current size of LRU cache"""

		return len(self.__cache)

	def clear(self):
		"""Clear pool storage"""

		self.__cache.clear()

	def get(self, host, port=None):
		"""Get connection pool for single host"""

		pool_key = (host, port)

		pool = self.__cache.get(pool_key)
		if pool:
			return pool

		pool = self.SingleHostPoolCls(
			lambda: self.__connection_factory(host, port),
			pool_size=self.__pool_size, pool_block = self.__pool_block, pool_timeout = self.__pool_timeout)
		self.__cache[pool_key] = pool

		return pool
