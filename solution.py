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
    def __init__(self, capacity: int, priority=False, fair=False) -> None:
        self.capacity = capacity
        self.q = deque()
        self.counter = 0
        self.pq = []
        self.priority = priority
        self.condition = threading.Condition()
        self.fair = fair
        self.lock = threading.Lock()
        self.producer_waiters = deque()
        self.consumer_waiters = deque()
        self.blocked_producer_count = 0  # for non-fair mode, this is just an approximation of how many producers are blocked because we don't want to acquire lock in put() if not necessary, but for fair mode, this is exact because producers will always acquire lock and append to producer_waiters before blocking
        self.blocked_consumer_count = 0  # for non-fair mode, this is just an approximation of how many consumers are blocked because we don't want to acquire lock in take() if not necessary, but for fair mode, this is exact because consumers will always acquire lock and append to consumer_waiters before blocking
        self.queue_metrics = {
            "total_puts": 0,
            "total_takes": 0,
            "total_timeouts": 0,
            "total_drains": 0,
            "items_drained": 0,
            "peak_size": 0,
        }

    def put(self, item, timeout=None):
        with self.condition:
            if not self.fair:
                if timeout is None:
                    while self.is_full():
                        self.blocked_producer_count += 1
                        self.condition.wait()
                        self.blocked_producer_count -= 1
                else:
                    deadline = time.time() + max(0, timeout)
                    while self.is_full():
                        remaining = deadline - time.time()
                        if remaining <= 0:
                            self.queue_metrics["total_timeouts"] += 1
                            return False
                        self.blocked_producer_count += 1
                        self.condition.wait(remaining)
                        self.blocked_producer_count -= 1

                self._insert(item)
                self.condition.notify_all()
                return True
            else:
                deadline = (
                    time.time() + max(0, timeout) if timeout is not None else None
                )
                event = threading.Event()
                with self.lock:
                    self.producer_waiters.append(event)

                while True:
                    with self.lock:
                        if not self.is_full():
                            self.producer_waiters.remove(event)
                            self._insert(item)
                            self._notify_consumer()
                            return True

                    remaining = (deadline - time.time()) if deadline else None
                    if remaining is not None and remaining <= 0:
                        with self.lock:
                            if event in self.producer_waiters:
                                self.producer_waiters.remove(event)
                            self.queue_metrics["total_timeouts"] += 1
                        return False
                    event.wait(timeout=remaining)
                    event.clear()  # clear the set state or otherwise it wouldn't wait again because its set() was called by producer

    def _notify_consumer(self):
        if self.consumer_waiters:
            self.consumer_waiters[0].set()

    def _notify_producer(self):
        if self.producer_waiters:
            self.producer_waiters[0].set()

    def _insert(self, item):
        if self.priority:
            priority, value = item
            heapq.heappush(self.pq, (priority, self.counter, value))
        else:
            self.q.append(item)
        self.queue_metrics["total_puts"] += 1
        self.queue_metrics["peak_size"] = max(
            self.queue_metrics["peak_size"], len(self._get_q())
        )
        self.counter += 1

    def take(self, timeout=None):
        if not self.fair:
            with self.condition:
                if timeout is None:
                    while self.is_empty():
                        self.blocked_consumer_count += 1
                        self.condition.wait()
                        self.blocked_consumer_count -= 1
                else:
                    deadline = time.time() + max(0, timeout)
                    while self.is_empty():
                        remaining = deadline - time.time()
                        if remaining <= 0:
                            self.queue_metrics["total_timeouts"] += 1
                            return None

                        self.blocked_consumer_count += 1
                        self.condition.wait(remaining)
                        self.blocked_consumer_count -= 1

                val = self._pop()
                self.condition.notify_all()
                return val
        else:
            deadline = time.time() + max(0, timeout) if timeout is not None else None
            event = threading.Event()
            with self.lock:
                self.consumer_waiters.append(event)

            while True:
                with self.lock:
                    if not self.is_empty():
                        self.consumer_waiters.remove(event)
                        val = self._pop()
                        self._notify_producer()
                        return val

                remaining = (deadline - time.time()) if deadline else None
                if remaining and remaining <= 0:
                    with self.lock:
                        self.queue_metrics["total_timeouts"] += 1
                        self.consumer_waiters.remove(event)
                        return None

                event.wait(timeout=remaining)
                event.clear()  # clear the set state or otherwise it wouldn't wait again because its set() was called by producer

    def _pop(self):
        self.queue_metrics["total_takes"] += 1
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
        self.queue_metrics["total_drains"] += 1
        with self.condition:
            items = []
            if self.priority:
                while self.pq:
                    items.append(self._format_priority_item(heapq.heappop(self.pq)))
            else:
                while self.q:
                    items.append(self.q.popleft())

            self.queue_metrics["items_drained"] += len(items)
            if self.fair:
                self._notify_producer()  # if there are producers waiting, notify one of them to put more items after draining, but we don't notify consumers because we just drained all items so there is nothing to consume
            else:
                self.condition.notify_all()
            return items

    def metrics(self):
        historical_metric = self.queue_metrics
        return {
            **historical_metric,
            "current_size": self.size(),
            "blocked_producers": (
                len(self.producer_waiters) if self.fair else self.blocked_producer_count
            ),
            "blocked_consumers": (
                len(self.consumer_waiters) if self.fair else self.blocked_consumer_count
            ),
        }
