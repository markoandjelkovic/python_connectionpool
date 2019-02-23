import unittest
import threading

from connectionpool import connectionpool


class FakeGoodConnection(connectionpool.ConnectionWrapper):
	def ok(self):
		return True


class FakeConnectionFactory:
	def __init__(self):
		self.counter = 0
		self.host = None
		self.port = None

	def __call__(self, host, port):
		self.counter += 1
		self.host = host
		self.port = port
		return connectionpool.ConnectionWrapper(self.counter)


class TestConnectionPool(unittest.TestCase):

	def test_init_with_defaults(self):
		pool = connectionpool.ConnectionPool(connection_factory=FakeConnectionFactory)
		self.assertEquals(pool.get_cache_max_size(), 100)
		self.assertEquals(pool.get_cache_cur_size(), 0)
		self.assertEquals(pool.get("host").get_pool_size(), 1)

	def test_connection_reuse(self):
		connection_factory = FakeConnectionFactory()
		pool = connectionpool.ConnectionPool(connection_factory=connection_factory)
		def _callback(conn):
			return conn.conn
		self.assertEquals(pool.get("host", "port").request(_callback), 1)
		self.assertEquals(connection_factory.host, "host")
		self.assertEquals(connection_factory.port, "port")
		self.assertEquals(pool.get("host", "port").request(_callback), 1)
		self.assertEquals(pool.get("host1", "port").request(_callback), 2)
		self.assertEquals(pool.get("host1", "port").request(_callback), 2)
		self.assertEquals(pool.get("host", "port1").request(_callback), 3)
		self.assertEquals(pool.get("host", "port1").request(_callback), 3)

	def test_connection_eviction(self):
		connection_factory = FakeConnectionFactory()
		pool = connectionpool.ConnectionPool(connection_factory=connection_factory, cache_size=1)
		def _callback(conn):
			return conn.conn
		self.assertEquals(pool.get_cache_cur_size(), 0)
		self.assertEquals(pool.get("host1").request(_callback), 1)
		self.assertEquals(pool.get_cache_cur_size(), 1)
		self.assertEquals(pool.get("host2").request(_callback), 2)
		self.assertEquals(pool.get_cache_cur_size(), 1)
		self.assertEquals(pool.get("host1").request(_callback), 3)
