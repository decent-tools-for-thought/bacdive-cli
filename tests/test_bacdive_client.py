from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from bacdive_cli.cache import DiskLRUCache
from bacdive_cli.client import BacdiveClient, BacdiveCliError


def test_fetch_builds_v2_path_and_uses_cache(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"ok": True, "path": request.url.path})

    client = BacdiveClient(
        cache=DiskLRUCache(root=tmp_path, max_bytes=4096),
        transport=httpx.MockTransport(handler),
    )
    try:
        first = client.fetch(["24493", "24494"], predictions=True)
        second = client.fetch(["24493", "24494"], predictions=True)
    finally:
        client.close()

    assert calls == ["https://api.bacdive.dsmz.de/v2/fetch/24493;24494?page=0&predictions=1"]
    assert first == second
    assert first["ok"] is True


def test_culture_collection_uses_search_type_and_page(tmp_path: Path) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"count": 1, "results": []})

    client = BacdiveClient(
        cache=DiskLRUCache(root=tmp_path, max_bytes=4096),
        transport=httpx.MockTransport(handler),
    )
    try:
        client.culture_collection(["DSM"], search_type="startswith", page=2, use_cache=False)
    finally:
        client.close()

    assert seen == [
        "https://api.bacdive.dsmz.de/v2/culturecollectionno/DSM?search_type=startswith&page=2"
    ]


def test_taxon_requires_species_before_subspecies(tmp_path: Path) -> None:
    client = BacdiveClient(cache=DiskLRUCache(root=tmp_path, max_bytes=4096))
    try:
        with pytest.raises(BacdiveCliError, match="subspecies requires species epithet"):
            client.taxon("Bacillus", subspecies_epithet="subtilis")
    finally:
        client.close()


def test_sequence_lookup_rejects_invalid_search_type(tmp_path: Path) -> None:
    client = BacdiveClient(cache=DiskLRUCache(root=tmp_path, max_bytes=4096))
    try:
        with pytest.raises(BacdiveCliError, match="search_type must be one of"):
            client.sequence_16s(["AF000162"], search_type="fuzzy")
    finally:
        client.close()
