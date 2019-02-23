import unittest
import threading

from connectionpool import lrucache


class TestLRUCache(unittest.TestCase):

	def test_clear_cache(self):
		cache = lrucache.LRUCache()
		cache[1] = "value"
		cache[2] = "value"
		cache.clear()
		self.assertTrue(1 not in cache)
		self.assertTrue(2 not in cache)
		self.assertEquals(cache.items(), [])

	def test_contains(self):
		cache = lrucache.LRUCache()
		self.assertTrue(1 not in cache)
		cache[1] = "value"
		self.assertTrue(1 in cache)

	def test_del_item(self):
		cache = lrucache.LRUCache()
		cache[1] = "value"
		cache[2] = "value"
		del cache[1]
		self.assertTrue(1 not in cache)
		self.assertTrue(2 in cache)
		self.assertEquals(cache.keys(), [ 2 ])

	def test_dispose_on_clear(self):
		disposed = set()
		def _disposefunc(item):
			disposed.add(item)
		cache = lrucache.LRUCache(disposefunc=_disposefunc)
		cache[1] = "value1"
		cache[2] = "value2"
		cache.clear()
		self.assertEquals(disposed, set(["value1", "value2"]))

	def test_dispose_on_delete(self):
		disposed = set()
		def _disposefunc(item):
			disposed.add(item)

		cache = lrucache.LRUCache(disposefunc=_disposefunc)
		cache[1] = "value1"
		cache[2] = "value2"

		del cache[1]
		self.assertEquals(disposed, set(["value1"]))

	def test_dispose_on_insert(self):
		disposed = set()
		def _disposefunc(item):
			disposed.add(item)

		cache = lrucache.LRUCache(cache_size=1, disposefunc=_disposefunc)
		cache[1] = "value1"
		cache[2] = "value2"
		self.assertEquals(disposed, set(["value1"]))

	def test_dispose_on_update(self):
		disposed = set()
		def _disposefunc(item):
			disposed.add(item)

		cache = lrucache.LRUCache(disposefunc=_disposefunc)
		cache[1] = "value1"
		cache[1] = "value2"
		self.assertEquals(disposed, set(["value1"]))

	def test_get_items(self):
		cache = lrucache.LRUCache()
		cache[1] = "value1"
		cache[2] = "value2"
		self.assertEquals(cache.items(), [(1, "value1"), (2, "value2")])

	def test_get_keys(self):
		cache = lrucache.LRUCache()
		cache[1] = "value1"
		cache[2] = "value2"
		self.assertEquals(cache.keys(), [1, 2])

	def test_get_len(self):
		cache = lrucache.LRUCache()
		cache[1] = "value"
		cache[2] = "value"
		self.assertEquals(len(cache), 2)

	def test_get_values(self):
		cache = lrucache.LRUCache()
		cache[1] = "value1"
		cache[2] = "value2"
		self.assertEquals(cache.values(), ["value1", "value2"])

	def test_init_with_defaults(self):
		cache = lrucache.LRUCache()
		self.assertEquals(cache.getsize(), 1000)
		self.assertEquals(cache.keys(), [])

	def test_iteration_on_cache(self):
		cache = lrucache.LRUCache()
		cache[1] = "value"
		cache[2] = "value"
		def iterate():
			for i in cache:
				self.fail("Iteration shouldn't be implemented")
		self.assertRaises(NotImplementedError, iterate)

	def test_multithread_delete(self):
		cache = lrucache.LRUCache()
		for i in xrange(10):
			cache[i] = i;

		def _delete(i):
			del cache[i]

		threads = [ threading.Thread(target=_delete, args=(i,)) for i in xrange(10) ]
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		for i in xrange(10):
			self.assertTrue(i not in cache)
		self.assertEquals(cache.keys(), [])

	def test_multithread_insert(self):
		cache = lrucache.LRUCache()
		def _insert(i):
			cache[i] = i
		threads = [ threading.Thread(target=_insert, args=(i,)) for i in xrange(10) ]
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		for i in xrange(10):
			self.assertTrue(i in cache)
		self.assertEquals(set(cache.keys()), set([i for i in xrange(10)]))

	def test_multithread_update(self):
		cache = lrucache.LRUCache()
		for i in xrange(10):
			cache[i] = i
		def _update(i):
			cache[i] = i + 10
		threads = [ threading.Thread(target=_update, args=(i,)) for i in xrange(10) ]
		for t in threads:
			t.start()
		for t in threads:
			t.join()
		for i in xrange(10):
			self.assertTrue(i in cache)
		self.assertEquals(set(cache.keys()), set([i for i in xrange(10)]))
		self.assertEquals(set(cache.values()), set([i + 10 for i in xrange(10)]))

	def test_reorder_on_get(self):
		cache = lrucache.LRUCache()
		cache[1] = "value"
		cache[2] = "value"

		value = cache[1]
		self.assertEquals(value,"value")
		self.assertTrue(1 in cache)
		self.assertTrue(2 in cache)
		self.assertEquals(cache.keys(), [ 2, 1 ])

	def test_reorder_on_insert(self):
		cache = lrucache.LRUCache()
		cache[1] = "value"
		cache[2] = "value"
		self.assertTrue(1 in cache)
		self.assertTrue(2 in cache)
		self.assertEquals(cache.keys(), [ 1, 2 ])

	def test_reorder_on_update(self):
		cache = lrucache.LRUCache()
		cache[1] = "value"
		cache[2] = "value"
		cache[1] = "newvalue"
		self.assertTrue(1 in cache)
		self.assertTrue(2 in cache)
		self.assertEquals(cache.keys(), [ 2, 1 ])

	def test_sizelimit_on_insert(self):
		cache = lrucache.LRUCache(cache_size=2)
		cache[1] = "value"
		cache[2] = "value"
		cache[3] = "value"
		self.assertTrue(1 not in cache)
		self.assertTrue(2 in cache)
		self.assertTrue(3 in cache)
		self.assertEquals(cache.keys(), [ 2, 3 ])
