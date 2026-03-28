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

            self.q.append(item)
            print(self.q)
            self.condition.notify_all()
            return True

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
            val = self.q.popleft()
            self.condition.notify_all()
            return val

    def peek(self):
        if self.is_empty():
            return None
        return self.q[0]

    def size(self):
        return len(self.q)

    def is_empty(self):
        return len(self.q) == 0

    def is_full(self):
        return len(self.q) == self.capacity
