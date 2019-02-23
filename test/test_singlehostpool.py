import unittest
import threading

from connectionpool import connectionpool


class FakeException(Exception):
	pass


class FakeGoodConnection(connectionpool.ConnectionWrapper):
	def ok(self):
		return True


class FakeBadConnection(connectionpool.ConnectionWrapper):
	def ok(self):
		return False


class FakeClosableConnection(connectionpool.ConnectionWrapper):
	def __init__(self, conn):
		connectionpool.ConnectionWrapper.__init__(self, conn)
		self.opened = True

	def close(self):
		self.opened = False

	def ok(self):
		return self.opened


class FakeConnectionFactory:
	def __init__(self, wrapper):
		self.counter = 0
		self.wrapper = wrapper

	def __call__(self):
		self.counter += 1
		return self.wrapper(self.counter)


class TestSingleConnectionHostPool(unittest.TestCase):

	def test_init_with_defaults(self):
		pool = connectionpool.SingleHostConnectionPool(connection_factory=None)
		self.assertEquals(pool.get_pool_size(), 1)

	def test_connection_reuse(self):
		connection_factory = FakeConnectionFactory(FakeGoodConnection)

		def _callback(conn):
			self.assertTrue(isinstance(conn, FakeGoodConnection))
			return conn.conn

		pool = connectionpool.SingleHostConnectionPool(connection_factory=connection_factory)
		self.assertEquals(pool.request(_callback), 1)
		self.assertEquals(pool.request(_callback), 1) # should be same connection

	def test_connection_recreate_after_test(self):
		connection_factory = FakeConnectionFactory(FakeBadConnection)
		def _callback(conn):
			self.assertTrue(isinstance(conn, FakeBadConnection))
			return conn.conn
		pool = connectionpool.SingleHostConnectionPool(connection_factory=connection_factory)
		self.assertEquals(pool.request(_callback), 1)
		self.assertEquals(pool.request(_callback), 2)

	def test_connection_recreate_after_close(self):
		connection_factory = FakeConnectionFactory(FakeClosableConnection)

		def _callback(conn):
			conn.close()
			return conn.conn

		pool = connectionpool.SingleHostConnectionPool(connection_factory=connection_factory)
		self.assertEquals(pool.request(_callback), 1)
		self.assertEquals(pool.request(_callback), 2)

	def test_pool_exhausing(self):
		connection_factory = FakeConnectionFactory(FakeGoodConnection)
		pool = connectionpool.SingleHostConnectionPool(connection_factory=connection_factory, pool_size=1)

		def _failcallback(conn):
			self.fail("Connection pool should be exhausing at this point")

		def _callback(conn):
			# request another connection
			self.assertRaises(
				connectionpool.PoolIsEmptyError, lambda: pool.request(_failcallback))
		pool.request(_callback)

	def test_pool_closing(self):
		connection_factory = FakeConnectionFactory(FakeClosableConnection)

		def _callback(conn):
			return conn

		pool = connectionpool.SingleHostConnectionPool(connection_factory=connection_factory)
		conn = pool.request(_callback)
		self.assertTrue(conn.ok())
		pool.close()
		self.assertFalse(conn.ok())
		self.assertRaises(connectionpool.PoolIsClosedError, lambda: pool.request(_callback))

	def test_exception_from_callback(self):
		connection_factory = FakeConnectionFactory(FakeGoodConnection)

		def _callback(conn):
			raise FakeException()
			return conn

		pool = connectionpool.SingleHostConnectionPool(connection_factory=connection_factory)
		self.assertRaises(FakeException, lambda: pool.request(_callback))

	def test_recreate_request_from_callback(self):
		connection_factory = FakeConnectionFactory(FakeGoodConnection)

		class _Callback:
			def __init__(self):
				self.calls = 0
				self.connections = []
			def __call__(self, conn):
				self.calls += 1
				self.connections.append(conn.conn)
				raise connectionpool.PoolBrokenConnectionError(FakeException)
		_callback = _Callback()

		pool = connectionpool.SingleHostConnectionPool(connection_factory=connection_factory)
		self.assertRaises(FakeException, lambda: pool.request(_callback))
		self.assertEquals(_callback.calls, 2)
		self.assertEquals(_callback.connections, [1, 2])
