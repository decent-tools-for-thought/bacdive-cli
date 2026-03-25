from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .cache import DEFAULT_CACHE_MAX_BYTES, DiskLRUCache, default_cache_dir
from .client import SEARCH_TYPES, BacdiveClient, BacdiveCliError
from .docs import endpoint_names, render_docs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bacdive-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch detailed BacDive strain records")
    fetch_parser.add_argument("bacdive_ids", nargs="+")
    fetch_parser.add_argument("--predictions", action="store_true")
    _add_runtime_args(fetch_parser)

    culture_parser = subparsers.add_parser(
        "culture-collection",
        help="Search BacDive IDs by culture collection number",
    )
    culture_parser.add_argument("culture_collection_numbers", nargs="+")
    culture_parser.add_argument("--search-type", choices=list(SEARCH_TYPES), default="exact")
    _add_runtime_args(culture_parser)

    taxon_parser = subparsers.add_parser("taxon", help="Search BacDive IDs by taxonomy")
    taxon_parser.add_argument("genus")
    taxon_parser.add_argument("species_epithet", nargs="?")
    taxon_parser.add_argument("subspecies_epithet", nargs="?")
    _add_runtime_args(taxon_parser)

    seq16s_parser = subparsers.add_parser(
        "sequence-16s",
        help="Search BacDive IDs by 16S accession",
    )
    seq16s_parser.add_argument("accessions", nargs="+")
    seq16s_parser.add_argument("--search-type", choices=list(SEARCH_TYPES), default="exact")
    _add_runtime_args(seq16s_parser)

    genome_parser = subparsers.add_parser(
        "sequence-genome",
        help="Search BacDive IDs by genome accession",
    )
    genome_parser.add_argument("accessions", nargs="+")
    genome_parser.add_argument("--search-type", choices=list(SEARCH_TYPES), default="exact")
    _add_runtime_args(genome_parser)

    docs_parser = subparsers.add_parser(
        "docs",
        help="Show structured documentation for BacDive endpoints",
    )
    docs_parser.add_argument(
        "endpoint",
        nargs="?",
        default="all",
        choices=["all", *endpoint_names()],
    )
    docs_parser.add_argument(
        "--format",
        dest="output_format",
        choices=["markdown", "json"],
        default="markdown",
    )

    cache_parser = subparsers.add_parser("cache", help="Manage the BacDive response cache")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command", required=True)

    cache_stats = cache_subparsers.add_parser("stats", help="Show cache statistics")
    _add_cache_only_args(cache_stats)

    cache_prune = cache_subparsers.add_parser("prune", help="Evict old cache entries")
    _add_cache_only_args(cache_prune)

    cache_clear = cache_subparsers.add_parser("clear", help="Delete all cache entries")
    _add_cache_only_args(cache_clear)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "cache":
            return _run_cache(args)
        if args.command == "docs":
            return _run_docs(args)
        return _run_remote(args)
    except BacdiveCliError as error:
        parser.exit(status=2, message=f"error: {error}\n")
    return 0


def _run_remote(args: argparse.Namespace) -> int:
    cache = DiskLRUCache(root=args.cache_dir, max_bytes=_gigabytes_to_bytes(args.max_cache_size_gb))
    with BacdiveClient(base_url=args.base_url, cache=cache) as client:
        use_cache = not args.no_cache
        refresh = args.refresh
        if args.command == "fetch":
            payload = client.fetch(
                args.bacdive_ids,
                predictions=args.predictions,
                page=args.page,
                use_cache=use_cache,
                refresh=refresh,
            )
        elif args.command == "culture-collection":
            payload = client.culture_collection(
                args.culture_collection_numbers,
                search_type=args.search_type,
                page=args.page,
                use_cache=use_cache,
                refresh=refresh,
            )
        elif args.command == "taxon":
            payload = client.taxon(
                args.genus,
                species_epithet=args.species_epithet,
                subspecies_epithet=args.subspecies_epithet,
                page=args.page,
                use_cache=use_cache,
                refresh=refresh,
            )
        elif args.command == "sequence-16s":
            payload = client.sequence_16s(
                args.accessions,
                search_type=args.search_type,
                page=args.page,
                use_cache=use_cache,
                refresh=refresh,
            )
        elif args.command == "sequence-genome":
            payload = client.sequence_genome(
                args.accessions,
                search_type=args.search_type,
                page=args.page,
                use_cache=use_cache,
                refresh=refresh,
            )
        else:
            raise BacdiveCliError(f"unsupported command: {args.command}")
    _write_remote_result(args.output_format, payload)
    return 0


def _run_cache(args: argparse.Namespace) -> int:
    max_bytes = _gigabytes_to_bytes(args.max_size_gb)
    cache = DiskLRUCache(root=args.cache_dir, max_bytes=max_bytes)
    if args.cache_command == "stats":
        stats = cache.stats()
    elif args.cache_command == "prune":
        stats = cache.prune()
    elif args.cache_command == "clear":
        cache.clear()
        stats = cache.stats()
    else:
        raise BacdiveCliError(f"unsupported cache command: {args.cache_command}")
    print(
        json.dumps(
            {
                "cache_dir": str(args.cache_dir),
                "entries": stats.entries,
                "total_bytes": stats.total_bytes,
                "max_bytes": stats.max_bytes,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _run_docs(args: argparse.Namespace) -> int:
    print(render_docs(args.endpoint, args.output_format), end="")
    if args.output_format != "markdown":
        print()
    return 0


def _add_runtime_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--page", type=int, default=0)
    parser.add_argument("--format", dest="output_format", choices=["json", "raw"], default="json")
    parser.add_argument("--cache-dir", type=Path, default=default_cache_dir())
    parser.add_argument(
        "--max-cache-size-gb",
        type=float,
        default=DEFAULT_CACHE_MAX_BYTES / 1024**3,
    )
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--refresh", action="store_true")


def _add_cache_only_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cache-dir", type=Path, default=default_cache_dir())
    parser.add_argument(
        "--max-size-gb",
        type=float,
        default=DEFAULT_CACHE_MAX_BYTES / 1024**3,
    )


def _write_remote_result(output_format: str, payload: object) -> None:
    if output_format == "raw":
        print(json.dumps(payload))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def _gigabytes_to_bytes(size_gb: float) -> int:
    if size_gb <= 0:
        raise BacdiveCliError("cache size must be positive")
    return int(size_gb * 1024**3)
