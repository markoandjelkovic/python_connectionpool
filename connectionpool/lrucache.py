# Simple LRU cache based on idea derived from
# http://stackoverflow.com/questions/4443920/python-building-a-lru-cache
#
# This module is part of python-connectionpool and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php


import collections
import threading

class LRUCache(collections.MutableMapping):
	"""Simple LRU Cache with dict like interface"""

	def __init__(self, cache_size=1000, disposefunc=None):
		PREV, NEXT, KEY, VALUE = 0, 1, 2, 3

		self.__cache_size = cache_size
		self.__cache = {}
		self.__disposefunc = disposefunc

		self.__head = [ None, None, None, None ]        # oldest
		self.__tail = [ self.__head, None, None, None ]   # newest
		self.__head[NEXT] = self.__tail

		self.__lock = threading.Lock()

	def __contains__(self, key):
		return (key in self.__cache)

	def __delitem__(self, key, PREV=0, NEXT=1, KEY=2, VALUE=3):
		with self.__lock:
			oldlink = self.__cache.pop(key)
			oldlink_prev, oldlink_next, oldkey, oldvalue = oldlink
			oldlink_prev[NEXT] = oldlink_next
			oldlink_next[PREV] = oldlink_prev
		if self.__disposefunc:
			self.__disposefunc(oldvalue)

	def __getitem__(self, key, PREV=0, NEXT=1, KEY=2, VALUE=3):
		cache, head, tail = self.__cache, self.__head, self.__tail

		with self.__lock:
			link = cache[key]
			link_prev, link_next, key, value = link
			link_prev[NEXT] = link_next
			link_next[PREV] = link_prev
			last = tail[PREV]
			last[NEXT] = tail[PREV] = link
			link[PREV] = last
			link[NEXT] = tail

			return link[VALUE]

	def __iter__(self):
		raise NotImplementedError("Iteration over this class is unlikely to be threadsafe.")

	def __len__(self):
		with self.__lock:
			return len(self.__cache)

	def __setitem__(self, key, value, PREV=0, NEXT=1, KEY=2, VALUE=3, sentinel=object()):
		cache, head, tail = self.__cache, self.__head, self.__tail

		oldlink = sentinel
		with self.__lock:
			oldlink = cache.get(key, sentinel)
			if oldlink is not sentinel:
				oldlink_prev, oldlink_next, oldkey, oldvalue = oldlink
				oldlink_prev[NEXT] = oldlink_next
				oldlink_next[PREV] = oldlink_prev

			if len(cache) >= self.__cache_size:
				oldlink = head[NEXT]
				oldlink_prev, oldlink_next, oldkey, oldvalue = oldlink
				head[NEXT] = oldlink_next
				oldlink_next[PREV] = head
				del cache[oldkey]

			last = tail[PREV]
			link = [last, tail, key, value]
			cache[key] = last[NEXT] = tail[PREV] = link

		if oldlink is not sentinel and self.__disposefunc:
			self.__disposefunc(oldvalue)

	def clear(self):
		PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
		cache = self.__cache

		with self.__lock:
			oldlinks = cache.values()
			cache.clear()

			self.__head = [ None, None, None, None ]
			self.__tail = [ self.__head, None, None, None ]
			self.__head[NEXT] = self.__tail

		if self.__disposefunc:
			for oldlink in oldlinks:
				self.__disposefunc(oldlink[VALUE])

	def items(self):
		PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
		head, tail = self.__head, self.__tail

		with self.__lock:
			item = head[NEXT]
			result = []
			while item is not tail:
				result.append((item[KEY], item[VALUE]))
				item = item[NEXT]
			return result

	def getsize(self):
		return self.__cache_size

	def keys(self):
		return [ i[0] for i in self.items() ]

	def values(self):
		return [ i[1] for i in self.items() ]
