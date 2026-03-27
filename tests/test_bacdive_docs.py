from __future__ import annotations

import json

from bacdive_cli.docs import render_docs


def test_render_docs_json_for_single_endpoint() -> None:
    payload = json.loads(render_docs("fetch", "json"))

    assert payload["kind"] == "bacdive_cli_endpoint_docs"
    assert payload["observed_on"] == "2026-03-24"
    assert len(payload["endpoints"]) == 1
    assert payload["endpoints"][0]["command"] == "fetch"


def test_render_docs_markdown_contains_endpoint_sections() -> None:
    rendered = render_docs("all", "markdown")

    assert "# BacDive CLI Endpoint Documentation" in rendered
    assert "## Endpoint: fetch" in rendered
    assert "## Endpoint: taxon" in rendered
    assert "- observed_on: 2026-03-24" in rendered
    assert "bacdive taxon Bacillus subtilis returned count=286" in rendered
    assert "Observed on 2026-03-24" not in rendered
