"""Tests for the in-memory receipt cache."""

import time
from cache.receipt_cache import ReceiptCache


SAMPLE_RECEIPT = {
    "merchant": "Test Store",
    "date": "2026-04-18",
    "total": 42.50,
    "currency": "USD",
    "tax": 3.50,
    "items": [
        {"name": "Item A", "price": 20.00},
        {"name": "Item B", "price": 22.50},
    ],
    "category": "groceries",
}


class TestReceiptCache:
    """Unit tests for ReceiptCache."""

    def test_set_and_get(self):
        cache = ReceiptCache()
        rid = cache.generate_id()
        cache.set(rid, SAMPLE_RECEIPT)

        result = cache.get(rid)
        assert result is not None
        assert result["merchant"] == "Test Store"
        assert result["total"] == 42.50

    def test_get_nonexistent_returns_none(self):
        cache = ReceiptCache()
        assert cache.get("nonexistent-id") is None

    def test_delete(self):
        cache = ReceiptCache()
        rid = cache.generate_id()
        cache.set(rid, SAMPLE_RECEIPT)

        assert cache.delete(rid) is True
        assert cache.get(rid) is None

    def test_delete_nonexistent_returns_false(self):
        cache = ReceiptCache()
        assert cache.delete("nonexistent-id") is False

    def test_ttl_expiration(self):
        cache = ReceiptCache(default_ttl=1)  # 1 second TTL
        rid = cache.generate_id()
        cache.set(rid, SAMPLE_RECEIPT)

        # Should exist immediately
        assert cache.get(rid) is not None

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get(rid) is None

    def test_custom_ttl_per_entry(self):
        cache = ReceiptCache(default_ttl=600)
        rid = cache.generate_id()
        cache.set(rid, SAMPLE_RECEIPT, ttl=1)

        assert cache.get(rid) is not None
        time.sleep(1.1)
        assert cache.get(rid) is None

    def test_cleanup_expired(self):
        cache = ReceiptCache(default_ttl=1)
        for _ in range(5):
            cache.set(cache.generate_id(), SAMPLE_RECEIPT)

        assert cache.size == 5
        time.sleep(1.1)
        removed = cache.cleanup_expired()
        assert removed == 5
        assert cache.size == 0

    def test_size_property(self):
        cache = ReceiptCache()
        assert cache.size == 0
        cache.set(cache.generate_id(), SAMPLE_RECEIPT)
        assert cache.size == 1

    def test_unique_ids(self):
        cache = ReceiptCache()
        ids = {cache.generate_id() for _ in range(100)}
        assert len(ids) == 100  # All unique
