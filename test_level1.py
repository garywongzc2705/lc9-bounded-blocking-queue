"""
Level 1 — Bounded Blocking Queue

Implement a thread-safe bounded blocking queue.

Constructor:
  BoundedBlockingQueue(capacity)
    — capacity is the maximum number of items in the queue
    — capacity >= 1

Methods:
  queue.put(item)
    — add item to the back of the queue
    — if the queue is full, BLOCK until space becomes available
    — then add the item and return

  queue.take()
    — remove and return the item from the front of the queue
    — if the queue is empty, BLOCK until an item becomes available
    — then remove and return it

  queue.size()
    — return the current number of items in the queue
    — non-blocking, always returns immediately

  queue.is_empty()
    — return True if the queue has no items

  queue.is_full()
    — return True if the queue is at capacity

Semantics:
  - FIFO ordering — first item put is first item taken
  - Thread-safe — multiple threads can call put/take concurrently
  - put() on a full queue blocks until take() creates space
  - take() on an empty queue blocks until put() adds an item
  - capacity=1 is valid
"""

import pytest
import threading
import time
from solution import BoundedBlockingQueue


# --- Basic functionality ---

def test_put_and_take():
    q = BoundedBlockingQueue(3)
    q.put(1)
    assert q.take() == 1


def test_fifo_order():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.put(2)
    q.put(3)
    assert q.take() == 1
    assert q.take() == 2
    assert q.take() == 3


def test_size_empty():
    q = BoundedBlockingQueue(3)
    assert q.size() == 0


def test_size_after_put():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.put(2)
    assert q.size() == 2


def test_size_after_take():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.put(2)
    q.take()
    assert q.size() == 1


def test_is_empty_true():
    q = BoundedBlockingQueue(3)
    assert q.is_empty() is True


def test_is_empty_false():
    q = BoundedBlockingQueue(3)
    q.put(1)
    assert q.is_empty() is False


def test_is_full_false():
    q = BoundedBlockingQueue(3)
    q.put(1)
    assert q.is_full() is False


def test_is_full_true():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.put(2)
    q.put(3)
    assert q.is_full() is True


def test_capacity_one():
    q = BoundedBlockingQueue(1)
    q.put(42)
    assert q.take() == 42


# --- Blocking behavior ---

def test_take_blocks_when_empty():
    q = BoundedBlockingQueue(3)
    result = []

    def consumer():
        result.append(q.take())

    t = threading.Thread(target=consumer)
    t.start()
    time.sleep(0.05)
    assert result == []   # still blocking
    q.put(99)
    t.join(timeout=1.0)
    assert result == [99]


def test_put_blocks_when_full():
    q = BoundedBlockingQueue(2)
    q.put(1)
    q.put(2)
    put_done = threading.Event()

    def producer():
        q.put(3)   # should block
        put_done.set()

    t = threading.Thread(target=producer)
    t.start()
    time.sleep(0.05)
    assert not put_done.is_set()   # still blocking
    q.take()
    t.join(timeout=1.0)
    assert put_done.is_set()


def test_multiple_producers_consumers():
    q = BoundedBlockingQueue(3)
    results = []
    lock = threading.Lock()

    def producer(items):
        for item in items:
            q.put(item)

    def consumer(count):
        for _ in range(count):
            with lock:
                results.append(q.take())

    producers = [
        threading.Thread(target=producer, args=([1, 2, 3],)),
        threading.Thread(target=producer, args=([4, 5, 6],)),
    ]
    consumers = [
        threading.Thread(target=consumer, args=(3,)),
        threading.Thread(target=consumer, args=(3,)),
    ]

    for t in producers + consumers:
        t.start()
    for t in producers + consumers:
        t.join(timeout=2.0)

    assert sorted(results) == [1, 2, 3, 4, 5, 6]


def test_no_items_lost_under_concurrency():
    q = BoundedBlockingQueue(5)
    n = 50
    produced = list(range(n))
    consumed = []
    lock = threading.Lock()

    def producer():
        for item in produced:
            q.put(item)

    def consumer():
        for _ in range(n):
            item = q.take()
            with lock:
                consumed.append(item)

    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    t1.start()
    t2.start()
    t1.join(timeout=3.0)
    t2.join(timeout=3.0)

    assert sorted(consumed) == produced
