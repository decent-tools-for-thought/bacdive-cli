from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any
from urllib.parse import quote

import httpx

from .cache import DEFAULT_CACHE_MAX_BYTES, DiskLRUCache, default_cache_dir

DEFAULT_BASE_URL = "https://api.bacdive.dsmz.de"
DEFAULT_TIMEOUT_SECONDS = 30.0

SEARCH_TYPES = ("exact", "contains", "startswith", "endswith")
QueryParamValue = str | int | float | bool | None | Sequence[str | int | float | bool | None]


class BacdiveCliError(Exception):
    pass


def _encode_segments(values: Sequence[str]) -> str:
    return ";".join(quote(value, safe="") for value in values)


class BacdiveClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        cache: DiskLRUCache | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or base_url_from_env() or DEFAULT_BASE_URL).rstrip("/")
        self.cache = cache or DiskLRUCache(
            root=default_cache_dir(),
            max_bytes=int(os.environ.get("BACDIVE_CACHE_MAX_BYTES", DEFAULT_CACHE_MAX_BYTES)),
        )
        self.cache_ttl_seconds = cache_ttl_seconds
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> BacdiveClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def fetch(
        self,
        bacdive_ids: Sequence[str | int],
        *,
        predictions: bool = False,
        page: int = 0,
        use_cache: bool = True,
        refresh: bool = False,
    ) -> Any:
        ids = [str(value) for value in dict.fromkeys(bacdive_ids)]
        if not ids:
            raise BacdiveCliError("provide at least one BacDive ID")
        if len(ids) > 100:
            raise BacdiveCliError("BacDive accepts at most 100 IDs per fetch request")
        return self._request_json(
            f"/v2/fetch/{_encode_segments(ids)}",
            params={"page": page, "predictions": 1 if predictions else 0},
            use_cache=use_cache,
            refresh=refresh,
        )

    def culture_collection(
        self,
        culture_collection_numbers: Sequence[str],
        *,
        search_type: str = "exact",
        page: int = 0,
        use_cache: bool = True,
        refresh: bool = False,
    ) -> Any:
        values = list(dict.fromkeys(culture_collection_numbers))
        if not values:
            raise BacdiveCliError("provide at least one culture collection number")
        if search_type == "exact" and len(values) > 100:
            raise BacdiveCliError("BacDive accepts at most 100 exact culture collection numbers")
        self._validate_search_type(search_type)
        return self._request_json(
            f"/v2/culturecollectionno/{_encode_segments(values)}",
            params={"search_type": search_type, "page": page},
            use_cache=use_cache,
            refresh=refresh,
        )

    def taxon(
        self,
        genus: str,
        *,
        species_epithet: str | None = None,
        subspecies_epithet: str | None = None,
        page: int = 0,
        use_cache: bool = True,
        refresh: bool = False,
    ) -> Any:
        if not genus:
            raise BacdiveCliError("genus is required")
        parts = [genus]
        if species_epithet is not None:
            parts.append(species_epithet)
        if subspecies_epithet is not None:
            if species_epithet is None:
                raise BacdiveCliError("subspecies requires species epithet")
            parts.append(subspecies_epithet)
        path = "/v2/taxon/" + "/".join(quote(part, safe="") for part in parts)
        return self._request_json(
            path,
            params={"page": page},
            use_cache=use_cache,
            refresh=refresh,
        )

    def sequence_16s(
        self,
        accessions: Sequence[str],
        *,
        search_type: str = "exact",
        page: int = 0,
        use_cache: bool = True,
        refresh: bool = False,
    ) -> Any:
        return self._sequence_lookup(
            endpoint="sequence_16s",
            accessions=accessions,
            search_type=search_type,
            page=page,
            use_cache=use_cache,
            refresh=refresh,
        )

    def sequence_genome(
        self,
        accessions: Sequence[str],
        *,
        search_type: str = "exact",
        page: int = 0,
        use_cache: bool = True,
        refresh: bool = False,
    ) -> Any:
        return self._sequence_lookup(
            endpoint="sequence_genome",
            accessions=accessions,
            search_type=search_type,
            page=page,
            use_cache=use_cache,
            refresh=refresh,
        )

    def _sequence_lookup(
        self,
        *,
        endpoint: str,
        accessions: Sequence[str],
        search_type: str,
        page: int,
        use_cache: bool,
        refresh: bool,
    ) -> Any:
        values = list(dict.fromkeys(accessions))
        if not values:
            raise BacdiveCliError("provide at least one accession")
        if search_type == "exact" and len(values) > 100:
            raise BacdiveCliError("BacDive accepts at most 100 exact accession values")
        self._validate_search_type(search_type)
        return self._request_json(
            f"/v2/{endpoint}/{_encode_segments(values)}",
            params={"search_type": search_type, "page": page},
            use_cache=use_cache,
            refresh=refresh,
        )

    def _validate_search_type(self, search_type: str) -> None:
        if search_type not in SEARCH_TYPES:
            allowed = ", ".join(SEARCH_TYPES)
            raise BacdiveCliError(f"search_type must be one of: {allowed}")

    def _request_json(
        self,
        path: str,
        *,
        params: dict[str, QueryParamValue],
        use_cache: bool,
        refresh: bool,
    ) -> Any:
        cache_key = self.cache.make_key(
            {"base_url": self.base_url, "path": path, "params": params}
        )
        if use_cache and not refresh:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return httpx.Response(200, content=cached).json()
        response = self._http.get(path, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = _extract_error_detail(response)
            raise BacdiveCliError(
                f"request failed with HTTP {response.status_code}: {response.request.url}{detail}"
            ) from exc
        if use_cache:
            self.cache.set(cache_key, response.content, ttl_seconds=self.cache_ttl_seconds)
        return response.json()


def _extract_error_detail(response: httpx.Response) -> str:
    body = response.text.strip()
    if not body:
        return ""
    try:
        parsed = response.json()
    except ValueError:
        return f": {body}"
    if isinstance(parsed, dict):
        for key in ("message", "error", "detail", "title"):
            value = parsed.get(key)
            if isinstance(value, str) and value:
                return f": {value}"
    return f": {parsed}"


def base_url_from_env() -> str | None:
    return os.environ.get("BACDIVE_API_BASE_URL")
