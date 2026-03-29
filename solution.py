from collections import deque
import threading
import time
import heapq

# Anthropic — Staff Engineer · Incremental Coding Round #10
# solution.py — Bounded Blocking Queue
#
# Write your implementation here.
# You may add any classes, functions, or methods you need.
# Do not import external libraries — stdlib only.
#
# Before each level, add a comment block explaining your approach:
#
# --- LEVEL 1 APPROACH ---
# (your design notes here)
# -------------------------


class BoundedBlockingQueue:
    def __init__(self, capacity: int, priority=False) -> None:
        self.capacity = capacity
        self.q = deque()
        self.counter = 0
        self.pq = []
        self.priority = priority
        self.condition = threading.Condition()

    def put(self, item, timeout=None):
        with self.condition:
            if timeout is None:
                while self.is_full():
                    self.condition.wait()
            else:
                deadline = time.time() + max(0, timeout)
                while self.is_full():
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        return False

                    self.condition.wait(remaining)

            self._insert(item)
            self.condition.notify_all()
            return True

    def _insert(self, item):
        if self.priority:
            priority, value = item
            heapq.heappush(self.pq, (priority, self.counter, value))
        else:
            self.q.append(item)
        self.counter += 1

    def take(self, timeout=None):
        with self.condition:
            if timeout is None:
                while self.is_empty():
                    self.condition.wait()
            else:
                deadline = time.time() + max(0, timeout)
                while self.is_empty():
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        return None
                    self.condition.wait(remaining)
            val = self._pop()
            self.condition.notify_all()
            return val

    def _pop(self):
        if self.priority:
            return self._format_priority_item(heapq.heappop(self.pq))
        else:
            return self.q.popleft()

    def peek(self):
        if self.is_empty():
            return None
        return (
            self._get_q()[0]
            if not self.priority
            else self._format_priority_item(self._get_q()[0])
        )

    def _format_priority_item(self, tuple):
        return (tuple[0], tuple[2])

    def size(self):
        return len(self._get_q())

    def is_empty(self):
        return len(self._get_q()) == 0

    def is_full(self):
        return len(self._get_q()) == self.capacity

    def _get_q(self):
        return self.q if not self.priority else self.pq

    def drain(self):
        with self.condition:
            items = []
            if self.priority:
                while self.pq:
                    items.append(self._format_priority_item(heapq.heappop(self.pq)))
            else:
                while self.q:
                    items.append(self.q.popleft())

            self.condition.notify_all()
            return items
