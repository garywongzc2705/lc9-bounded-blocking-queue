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
        self.lock = threading.Lock()

    def put(self, item):
        while True:
            with self.lock:
                if len(self.q) < self.capacity:
                    self.q.append(item)
                    return
            time.sleep(0.2)

    def take(self):
        while True:
            with self.lock:
                if len(self.q) > 0:
                    return self.q.popleft()
            time.sleep(0.2)

    def size(self):
        return len(self.q)

    def is_empty(self):
        return len(self.q) == 0

    def is_full(self):
        return len(self.q) == self.capacity
