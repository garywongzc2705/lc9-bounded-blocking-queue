"""
Level 3 — Priority Queue and Drain

Add priority-based ordering and bulk drain operation.

New constructor parameter:
  BoundedBlockingQueue(capacity, priority=False)
    — priority=False (default): FIFO ordering (existing behavior)
    — priority=True: items are taken in priority order
      Items are (priority, value) tuples.
      Lower priority number = higher urgency = taken first.
      Ties broken by insertion order (FIFO among equal priority).

Updated methods when priority=True:
  queue.put(item, timeout=None)
    — item must be a (priority, value) tuple
    — blocks if full (same as before)
    — returns True/False (same as before)

  queue.take(timeout=None)
    — returns the (priority, value) tuple with the lowest priority number
    — blocks if empty (same as before)
    — returns None on timeout (same as before)

  queue.peek()
    — returns the (priority, value) tuple that would be taken next
    — returns None if empty

New method:
  queue.drain()
    — remove and return ALL current items as a list
    — non-blocking — takes only what is currently in the queue
    — does not wait for more items
    — for FIFO queues: returns items in FIFO order
    — for priority queues: returns items in priority order
    — wakes any blocked producers after draining
      (draining frees capacity, so blocked puts can proceed)

Semantics:
  - priority=False queues are unaffected by this level
  - FIFO ordering is preserved among equal-priority items
  - drain() on empty queue returns []
  - drain() is atomic — no items can be added/removed during drain
  - all previous tests must pass
"""

import pytest
import threading
import time
from solution import BoundedBlockingQueue


# --- FIFO mode unchanged ---

def test_fifo_still_works():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.put(2)
    q.put(3)
    assert q.take() == 1
    assert q.take() == 2
    assert q.take() == 3


# --- Priority queue basics ---

def test_priority_takes_lowest_number_first():
    q = BoundedBlockingQueue(5, priority=True)
    q.put((3, "low"))
    q.put((1, "high"))
    q.put((2, "medium"))
    assert q.take() == (1, "high")
    assert q.take() == (2, "medium")
    assert q.take() == (3, "low")


def test_priority_fifo_tiebreak():
    q = BoundedBlockingQueue(5, priority=True)
    q.put((1, "first"))
    q.put((1, "second"))
    q.put((1, "third"))
    assert q.take() == (1, "first")
    assert q.take() == (1, "second")
    assert q.take() == (1, "third")


def test_priority_peek_returns_highest_priority():
    q = BoundedBlockingQueue(5, priority=True)
    q.put((3, "low"))
    q.put((1, "high"))
    assert q.peek() == (1, "high")
    assert q.size() == 2   # peek doesn't remove


def test_priority_blocks_when_full():
    q = BoundedBlockingQueue(2, priority=True)
    q.put((1, "a"))
    q.put((2, "b"))
    put_done = threading.Event()

    def producer():
        q.put((3, "c"))
        put_done.set()

    t = threading.Thread(target=producer)
    t.start()
    time.sleep(0.05)
    assert not put_done.is_set()
    q.take()
    t.join(timeout=1.0)
    assert put_done.is_set()


def test_priority_blocks_when_empty():
    q = BoundedBlockingQueue(3, priority=True)
    result = [None]

    def consumer():
        result[0] = q.take()

    t = threading.Thread(target=consumer)
    t.start()
    time.sleep(0.05)
    assert result[0] is None
    q.put((1, "hello"))
    t.join(timeout=1.0)
    assert result[0] == (1, "hello")


def test_priority_timeout_returns_none():
    q = BoundedBlockingQueue(3, priority=True)
    assert q.take(timeout=0.05) is None


def test_priority_mixed_priorities():
    q = BoundedBlockingQueue(10, priority=True)
    items = [(5, "e"), (2, "b"), (4, "d"), (1, "a"), (3, "c")]
    for item in items:
        q.put(item)
    results = [q.take() for _ in range(5)]
    assert results == [(1, "a"), (2, "b"), (3, "c"), (4, "d"), (5, "e")]


# --- drain() ---

def test_drain_returns_all_items():
    q = BoundedBlockingQueue(5)
    q.put(1)
    q.put(2)
    q.put(3)
    result = q.drain()
    assert result == [1, 2, 3]


def test_drain_empties_queue():
    q = BoundedBlockingQueue(5)
    q.put(1)
    q.put(2)
    q.drain()
    assert q.size() == 0
    assert q.is_empty()


def test_drain_empty_queue():
    q = BoundedBlockingQueue(5)
    assert q.drain() == []


def test_drain_fifo_order():
    q = BoundedBlockingQueue(5)
    q.put(10)
    q.put(20)
    q.put(30)
    assert q.drain() == [10, 20, 30]


def test_drain_priority_order():
    q = BoundedBlockingQueue(5, priority=True)
    q.put((3, "c"))
    q.put((1, "a"))
    q.put((2, "b"))
    result = q.drain()
    assert result == [(1, "a"), (2, "b"), (3, "c")]


def test_drain_wakes_blocked_producer():
    q = BoundedBlockingQueue(2)
    q.put(1)
    q.put(2)
    put_done = threading.Event()

    def producer():
        result = q.put(3)
        put_done.set()

    t = threading.Thread(target=producer)
    t.start()
    time.sleep(0.05)
    assert not put_done.is_set()
    q.drain()
    t.join(timeout=1.0)
    assert put_done.is_set()


def test_drain_non_blocking():
    q = BoundedBlockingQueue(3)
    # drain on empty or partial queue returns immediately
    start = time.time()
    q.drain()
    elapsed = time.time() - start
    assert elapsed < 0.05
