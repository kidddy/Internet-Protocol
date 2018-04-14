
import time
import collections


SIZE = 20


CacheEntry = collections.namedtuple('CacheEntry', [
    "added_time",  # time.time()
    "ttl",  # seconds to live: int
    "value"])


class Cache:
    def __init__(self):
        self._table = dict()  # domain_name => CacheEntry
        #  self._queue = Queue()  # for LRU implemantation TODO
        # TODO Many records in cache, PackageBuilder and Compressing

    def add(self, key, value, ttl):
        pass  # TODO Add mutex lock and LRU
        added = time.time()
        self._table[key] = CacheEntry(added, ttl, value)

    def get(self, key):
        pass  # TODO Mutex lock
        if not self.fresh(key):
            return None
        pass  # TODO LRU shift
        return self._table[key].value

    def fresh(self, key):
        """Check if key is fresh. If not fresh then delete value in cache by the key."""
        if key not in self._table: return False
        entry = self._table[key]
        curr_time = time.time()
        dt = curr_time - entry.added_time
        if dt >= entry.ttl:
            del self._table[key]
            return False
        return True

    def contains(self, key):
        return key in self._table

    def refresh(self):
        pass  # TODO Mutex lock
        for key in self._table:
            fresh()
