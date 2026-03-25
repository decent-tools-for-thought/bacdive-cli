from __future__ import annotations

from pathlib import Path

from bacdive_cli.cache import DiskLRUCache


def test_cache_round_trip(tmp_path: Path) -> None:
    cache = DiskLRUCache(root=tmp_path, max_bytes=4096)
    key = cache.make_key({"path": "/v2/fetch/24493", "page": 0})

    cache.set(key, b'{"count":1}')

    assert cache.get(key) == b'{"count":1}'
