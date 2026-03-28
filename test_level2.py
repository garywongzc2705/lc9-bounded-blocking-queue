"""
Level 2 — Timeout Support

Add optional timeout parameters to put() and take() so callers
can avoid blocking indefinitely.

Updated methods:
  queue.put(item, timeout=None)
    — if timeout is None: block indefinitely until space is available (existing behavior)
    — if timeout is a number: block for at most timeout seconds
    — if space becomes available within timeout: add item, return True
    — if timeout expires before space is available: do NOT add item, return False

  queue.take(timeout=None)
    — if timeout is None: block indefinitely until an item is available (existing behavior)
    — if timeout is a number: block for at most timeout seconds
    — if an item becomes available within timeout: remove and return it
    — if timeout expires before an item is available: return None

New method:
  queue.peek()
    — return the front item WITHOUT removing it
    — if the queue is empty, return None
    — non-blocking, always returns immediately
    — does NOT count as a take

Semantics:
  - timeout=0 means try once immediately, don't block at all
  - timeout=0 on put() to a full queue returns False immediately
  - timeout=0 on take() from an empty queue returns None immediately
  - negative timeout behaves like timeout=0
  - All previous tests must pass
"""

import pytest
import threading
import time
from solution import BoundedBlockingQueue


# --- put() with timeout ---


def test_put_timeout_succeeds_when_space_available():
    q = BoundedBlockingQueue(3)
    result = q.put(1, timeout=1.0)
    assert result is True
    assert q.size() == 1


def test_put_timeout_returns_false_when_full():
    q = BoundedBlockingQueue(2)
    q.put(1)
    q.put(2)
    result = q.put(3, timeout=0.05)
    assert result is False
    assert q.size() == 2


def test_put_timeout_succeeds_when_space_opens():
    q = BoundedBlockingQueue(1)
    q.put(1)
    result_holder = [None]

    def producer():
        result_holder[0] = q.put(99, timeout=1.0)

    t = threading.Thread(target=producer)
    t.start()
    time.sleep(0.05)
    q.take()  # open space
    t.join(timeout=1.0)
    assert result_holder[0] is True
    assert q.size() == 1


def test_put_timeout_zero_full():
    q = BoundedBlockingQueue(1)
    q.put(1)
    assert q.put(2, timeout=0) is False


def test_put_timeout_zero_not_full():
    q = BoundedBlockingQueue(2)
    assert q.put(1, timeout=0) is True


def test_put_negative_timeout_behaves_like_zero():
    q = BoundedBlockingQueue(1)
    q.put(1)
    assert q.put(2, timeout=-1) is False


def test_put_none_timeout_still_blocks():
    q = BoundedBlockingQueue(1)
    q.put(1)
    put_done = threading.Event()

    def producer():
        q.put(99, timeout=None)
        put_done.set()

    t = threading.Thread(target=producer)
    t.start()
    time.sleep(0.05)
    assert not put_done.is_set()
    q.take()
    t.join(timeout=1.0)
    assert put_done.is_set()


# --- take() with timeout ---


def test_take_timeout_succeeds_when_item_available():
    q = BoundedBlockingQueue(3)
    q.put(42)
    result = q.take(timeout=1.0)
    assert result == 42


def test_take_timeout_returns_none_when_empty():
    q = BoundedBlockingQueue(3)
    result = q.take(timeout=0.05)
    assert result is None


def test_take_timeout_succeeds_when_item_arrives():
    q = BoundedBlockingQueue(3)
    result_holder = [None]

    def consumer():
        result_holder[0] = q.take(timeout=1.0)

    t = threading.Thread(target=consumer)
    t.start()
    time.sleep(0.05)
    q.put(77)
    t.join(timeout=1.0)
    assert result_holder[0] == 77


def test_take_timeout_zero_empty():
    q = BoundedBlockingQueue(3)
    assert q.take(timeout=0) is None


def test_take_timeout_zero_not_empty():
    q = BoundedBlockingQueue(3)
    q.put(5)
    assert q.take(timeout=0) == 5


def test_take_negative_timeout_behaves_like_zero():
    q = BoundedBlockingQueue(3)
    assert q.take(timeout=-1) is None


def test_take_none_timeout_still_blocks():
    q = BoundedBlockingQueue(3)
    take_done = threading.Event()
    result_holder = [None]

    def consumer():
        result_holder[0] = q.take(timeout=None)
        take_done.set()

    t = threading.Thread(target=consumer)
    t.start()
    time.sleep(0.05)
    assert not take_done.is_set()
    q.put(42)
    t.join(timeout=1.0)
    assert result_holder[0] == 42


# --- peek() ---


def test_peek_returns_front_item():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.put(2)
    assert q.peek() == 1


def test_peek_does_not_remove():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.peek()
    assert q.size() == 1
    assert q.take() == 1


def test_peek_empty_returns_none():
    q = BoundedBlockingQueue(3)
    assert q.peek() is None


def test_peek_does_not_affect_order():
    q = BoundedBlockingQueue(3)
    q.put(1)
    q.put(2)
    q.put(3)
    q.peek()
    q.peek()
    assert q.take() == 1
    assert q.take() == 2
    assert q.take() == 3
