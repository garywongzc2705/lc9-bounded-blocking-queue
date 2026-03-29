"""
Level 4 — Fair Scheduling and Metrics

Add two production features: fairness guarantees for waiting producers
and consumers, and observability metrics.

── Part A: Fair Scheduling ──────────────────────────────────────────

New constructor parameter:
  BoundedBlockingQueue(capacity, priority=False, fair=False)

  fair=False (default): existing behavior — no ordering guarantee
    among waiting producers or consumers
  fair=True: FIFO ordering among waiters — the longest-waiting
    producer gets the next available slot; the longest-waiting
    consumer gets the next available item

  Fairness semantics:
    - A fair queue prevents starvation — no producer or consumer
      can be indefinitely bypassed by later arrivals
    - Fairness applies to producers waiting on put() and consumers
      waiting on take() independently
    - fair=True with priority=True: items still taken in priority
      order, but among consumers waiting for items, the one that
      waited longest gets served first when an item arrives
    - timeout still works in fair mode — a timed-out waiter
      simply leaves the wait list

── Part B: Metrics ──────────────────────────────────────────────────

New method:
  queue.metrics()
    — return a dict of queue statistics:
      {
        "total_puts":         int,   # total successful put() calls
        "total_takes":        int,   # total successful take() calls
        "total_timeouts":     int,   # total put()/take() calls that timed out
        "total_drains":       int,   # total drain() calls
        "items_drained":      int,   # total items returned by drain()
        "peak_size":          int,   # maximum size ever reached
        "current_size":       int,   # current queue size
        "blocked_producers":  int,   # currently waiting on put()
        "blocked_consumers":  int,   # currently waiting on take()
      }

Semantics:
  - metrics are cumulative from construction
  - a put() that returns False (timeout) increments total_timeouts
  - a take() that returns None (timeout) increments total_timeouts
  - drain() counts as one drain regardless of items returned
  - peak_size updates on every successful put()
  - blocked_producers/consumers reflect current state at call time
  - all previous tests must pass
"""

import pytest
import threading
import time
from solution import BoundedBlockingQueue


# ── Part A: Fair Scheduling ───────────────────────────────────────────────────

def test_fair_put_fifo_ordering():
    """Producers waiting on a full queue are served in arrival order."""
    q = BoundedBlockingQueue(1, fair=True)
    q.put(0)   # fill the queue

    order = []
    lock = threading.Lock()
    ready = threading.Barrier(4)   # 3 producers + main thread

    def producer(val):
        ready.wait()
        q.put(val)
        with lock:
            order.append(val)

    threads = [threading.Thread(target=producer, args=(i,)) for i in range(1, 4)]
    for t in threads:
        t.start()

    ready.wait()
    time.sleep(0.1)   # let all producers block

    # drain one slot at a time, let each producer in
    for _ in range(3):
        q.take()
        time.sleep(0.05)

    for t in threads:
        t.join(timeout=2.0)

    assert order == [1, 2, 3]


def test_fair_take_fifo_ordering():
    """Consumers waiting on an empty queue are served in arrival order."""
    q = BoundedBlockingQueue(5, fair=True)

    order = []
    lock = threading.Lock()
    ready = threading.Barrier(4)

    def consumer(marker):
        ready.wait()
        val = q.take()
        with lock:
            order.append(marker)

    threads = [threading.Thread(target=consumer, args=(i,)) for i in range(1, 4)]
    for t in threads:
        t.start()

    ready.wait()
    time.sleep(0.1)   # let all consumers block

    for i in range(3):
        q.put(i)
        time.sleep(0.05)

    for t in threads:
        t.join(timeout=2.0)

    assert order == [1, 2, 3]


def test_fair_false_still_works():
    q = BoundedBlockingQueue(3, fair=False)
    q.put(1)
    q.put(2)
    assert q.take() == 1
    assert q.take() == 2


def test_fair_with_timeout():
    q = BoundedBlockingQueue(1, fair=True)
    q.put(1)
    result = q.put(2, timeout=0.05)
    assert result is False


# ── Part B: Metrics ───────────────────────────────────────────────────────────

@pytest.fixture
def q():
    return BoundedBlockingQueue(5)


def test_metrics_initial(q):
    m = q.metrics()
    assert m["total_puts"] == 0
    assert m["total_takes"] == 0
    assert m["total_timeouts"] == 0
    assert m["total_drains"] == 0
    assert m["items_drained"] == 0
    assert m["peak_size"] == 0
    assert m["current_size"] == 0
    assert m["blocked_producers"] == 0
    assert m["blocked_consumers"] == 0


def test_metrics_puts(q):
    q.put(1)
    q.put(2)
    assert q.metrics()["total_puts"] == 2


def test_metrics_takes(q):
    q.put(1)
    q.put(2)
    q.take()
    assert q.metrics()["total_takes"] == 1


def test_metrics_put_timeout(q):
    # fill it up
    for i in range(5):
        q.put(i)
    q.put(99, timeout=0.01)   # times out
    assert q.metrics()["total_timeouts"] == 1


def test_metrics_take_timeout(q):
    q.take(timeout=0.01)   # times out
    assert q.metrics()["total_timeouts"] == 1


def test_metrics_drain(q):
    q.put(1)
    q.put(2)
    q.put(3)
    q.drain()
    m = q.metrics()
    assert m["total_drains"] == 1
    assert m["items_drained"] == 3


def test_metrics_peak_size(q):
    q.put(1)
    q.put(2)
    q.put(3)
    q.take()
    assert q.metrics()["peak_size"] == 3


def test_metrics_current_size(q):
    q.put(1)
    q.put(2)
    q.take()
    assert q.metrics()["current_size"] == 1


def test_metrics_blocked_producers():
    q = BoundedBlockingQueue(1)
    q.put(1)   # fill it

    ready = threading.Event()
    def producer():
        ready.set()
        q.put(2)   # will block

    t = threading.Thread(target=producer)
    t.start()
    ready.wait()
    time.sleep(0.05)

    assert q.metrics()["blocked_producers"] == 1
    q.take()
    t.join(timeout=1.0)
    assert q.metrics()["blocked_producers"] == 0


def test_metrics_blocked_consumers():
    q = BoundedBlockingQueue(3)
    ready = threading.Event()

    def consumer():
        ready.set()
        q.take()   # will block

    t = threading.Thread(target=consumer)
    t.start()
    ready.wait()
    time.sleep(0.05)

    assert q.metrics()["blocked_consumers"] == 1
    q.put(1)
    t.join(timeout=1.0)
    assert q.metrics()["blocked_consumers"] == 0


def test_metrics_cumulative(q):
    q.put(1)
    q.put(2)
    q.take()
    q.drain()
    q.take(timeout=0.01)
    m = q.metrics()
    assert m["total_puts"] == 2
    assert m["total_takes"] == 1
    assert m["total_drains"] == 1
    assert m["total_timeouts"] == 1
