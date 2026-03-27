<div align="center">

# bacdive-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/bacdive-cli?sort=semver&color=0f766e)](https://github.com/decent-tools-for-thought/bacdive-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-0ea5e9)
![License](https://img.shields.io/badge/license-0BSD-14b8a6)

Command-line client for BacDive strain lookup, taxonomy search, accession-based discovery, offline endpoint docs, and optional local response caching.

</div>

> [!IMPORTANT]
> This codebase is entirely AI-generated. It is useful to me, I hope it might be useful to others, and issues and contributions are welcome.

## Map
- [Install](#install)
- [Functionality](#functionality)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Credits](#credits)

## Install
$$\color{#0EA5E9}Install \space \color{#14B8A6}Tool$$

```bash
uv tool install .      # install the CLI
bacdive-cli --help     # inspect the command surface
```

## Functionality
$$\color{#0EA5E9}Strain \space \color{#14B8A6}Lookup$$
- `bacdive-cli fetch <bacdive-id>...`: fetch one or more detailed BacDive strain records.
- `bacdive-cli fetch --predictions`: include prediction-oriented fields when available.
- `bacdive-cli fetch`: supports page selection, raw-vs-JSON output, cache bypass, refresh, cache directory overrides, and base URL overrides.

$$\color{#0EA5E9}Search \space \color{#14B8A6}Browse$$
- `bacdive-cli culture-collection <value>...`: resolve BacDive IDs from culture collection numbers.
- `bacdive-cli culture-collection --search-type exact|contains|startswith|endswith`: control BacDive string matching on supported search endpoints.
- `bacdive-cli taxon <genus> [species] [subspecies]`: search BacDive IDs by taxonomy terms.
- `bacdive-cli sequence-16s <accession>...`: search BacDive IDs by 16S accession.
- `bacdive-cli sequence-genome <accession>...`: search BacDive IDs by genome accession.

$$\color{#0EA5E9}Docs \space \color{#14B8A6}Inspect$$
- `bacdive-cli docs`: print structured endpoint documentation intended to be easy for both humans and LLMs to ingest.
- `bacdive-cli docs <endpoint>`: focus the docs output on one endpoint family.
- `bacdive-cli docs --format markdown|json`: emit either Markdown or machine-readable JSON.

$$\color{#0EA5E9}Cache \space \color{#14B8A6}Control$$
- `bacdive-cli cache stats`: show cache size and entry counts.
- `bacdive-cli cache prune --max-size-gb <n>`: evict older cache entries until the cache fits the target cap.
- `bacdive-cli cache clear`: remove all cached responses.

## Configuration
$$\color{#0EA5E9}Tune \space \color{#14B8A6}Defaults$$

By default the CLI targets `https://api.bacdive.dsmz.de`, uses the current `v2` endpoint family, pretty-prints JSON, and leaves response caching disabled.

- Use `--base-url` to target another BacDive deployment.
- Use `--format raw` to emit the unmodified response body.
- Use `--page` on paginated endpoints.
- Use `--max-cache-size-gb` with a value greater than `0` to enable local caching.
- Use `--no-cache` or `--refresh` when you want live responses instead of cached ones.

The main environment variables are `BACDIVE_API_BASE_URL`, `BACDIVE_CACHE_DIR`, `BACDIVE_CACHE_MAX_BYTES`, and `XDG_CACHE_HOME`.

### Config File
$$\color{#0EA5E9}Set \space \color{#14B8A6}Defaults$$

The CLI reads optional defaults from `$XDG_CONFIG_HOME/bacdive-cli/config.toml`, falling back to `~/.config/bacdive-cli/config.toml`.

Start from `config/default-config.toml` in this repo. The shipped default keeps caching off:

```toml
[cache]
max_size_gb = 0.0
```

## Quick Start
$$\color{#0EA5E9}Try \space \color{#14B8A6}Browse$$

```bash
bacdive-cli fetch 24493                                   # fetch one strain record
bacdive-cli fetch 24493 24494 --predictions               # fetch multiple records with predictions
bacdive-cli culture-collection "DSM 26640"                # resolve a culture collection number
bacdive-cli taxon Bacillus subtilis                       # search by taxonomy
bacdive-cli sequence-16s AF000162                         # search by 16S accession
bacdive-cli docs fetch --format json                      # inspect one endpoint family as JSON
```

## Credits

This client is built for the BacDive API and is not affiliated with DSMZ or BacDive.

Credit goes to the BacDive maintainers for the strain database, API surface, and endpoint documentation this tool builds on.
