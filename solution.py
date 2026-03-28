from collections import deque
import threading
import time

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
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.q = deque()
        self.condition = threading.Condition()

    def put(self, item):
        with self.condition:
            while self.is_full():
                self.condition.wait()
            self.q.append(item)
            self.condition.notify_all()

    def take(self):
        with self.condition:
            while self.is_empty():
                self.condition.wait()
            val = self.q.popleft()
            self.condition.notify_all()
            return val

    def size(self):
        return len(self.q)

    def is_empty(self):
        return len(self.q) == 0

    def is_full(self):
        return len(self.q) == self.capacity
