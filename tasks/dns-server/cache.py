
import time
import collections
import threading


class QueueEntry:
    def __init__(self, value):
        self.value = value
        self.next_node = None
        self.prev_node = None


class Queue:
    """Double linked queue with access to remove element from it or
    to readd."""

    def __init__(self):
        self._head = None
        self._tail = None

    @property
    def head(self):
        return self._head

    @property
    def tail(self):
        return self._tail

    def add(self, value):
        entry = QueueEntry(value)
        if self._head is None:
            self._head = entry
            self._tail = entry
        else:
            self._tail.next_node = entry
            entry.prev_node = self._tail
            self._tail = entry
        return entry

    def pop(self):
        if self.head == None:
            return None
        res_entry = self.head
        self._head = res_entry.next_node
        if self.head is not None:
            self._head.prev_node = None
        return res_entry.value

    def remove(self, entry: QueueEntry):
        if self.head == entry:
            if self.tail == entry:
                self._head = None
                self._tail = None
                return None
            self._head = self.head.next_node
            self._head.prev_node = None
        elif self.tail == entry:
            self._tail = self.tail.prev_node
            self._tail.next_node = None
        else:
            entry.prev_node.next_node = entry.next_node
            entry.next_node.prev_node = entry.prev_node

    def readd(self, entry: QueueEntry):
        value = entry.value
        self.remove(entry)
        return self.add(value)


SIZE = 20


CacheEntry = collections.namedtuple('CacheEntry', [
    "remove_time",
    "value"])


class Cache:
    def __init__(self):
        self._table = dict()  # key => CacheEntry
        self._lru_list = Queue()
        self._lru_entries = dict()  # key => QueueEntry
        self._lock = threading.Lock()

    def add(self, key, value, remove_time):
        """Add value to cache by the key. Will be removed when remove time.
        remove_time is result of time.time"""
        self._lock.acquire()
        try:
            lru_entry = self._lru_list.add(key)
            
            if not self.contains(key):
                self._table[key] = []
            self._table[key].append(CacheEntry(remove_time, value))
            self._lru_entries[key] = lru_entry
        finally:
            self._lock.release()

    def get(self, key):
        """Get a value by key. If value is out of time it will be removed"""
        self._lock.acquire()
        try:
            result = self.fresh(key)
            self.pop_down(key)
        finally:
            self._lock.release()
        return result

    def fresh(self, key):
        """Check if key is fresh. If not fresh then delete value
        in cache by the key
        
        """
        res = []
        if not self.contains(key):
            return res

        entry_list = self._table[key]
        curr_time = time.time()

        entry_idx = 0
        while entry_idx < len(entry_list):
            ttl = entry_list[entry_idx].remove_time - curr_time
            if ttl > 0:
                res.append((entry_list[entry_idx].value, int(ttl)))
                entry_idx += 1
            else: entry_list.pop(entry_idx)
        if len(entry_list) == 0: self.remove(key)
        return res

    def remove(self, key):
        self._lru_list.remove(self._lru_entries[key])
        del self._lru_entries[key]
        del self._table[key]

    def pop_down(self, key):
        """Readd key to LRU list"""
        if self.contains(key):
            self._lru_entries[key] = self._lru_list.readd(self._lru_entries[key])

    def contains(self, key):
        """Contains a key"""
        return key in self._table

    def refresh(self):
        self._lock.acquire()
        try:
            for key in self._table:
                self.fresh(key)
        finally:
            self._lock.release()

    @property
    def keys(self):
        yield from self._table.keys()
