from __future__ import annotations

import json
from pathlib import Path

import pytest

from bacdive_cli.core import build_parser, main


def test_parser_accepts_fetch_predictions_flag() -> None:
    args = build_parser().parse_args(["fetch", "24493", "--predictions"])

    assert args.command == "fetch"
    assert args.predictions is True
    assert args.page == 0


def test_main_writes_pretty_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class StubClient:
        def __enter__(self) -> StubClient:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def fetch(self, *_: object, **__: object) -> dict[str, object]:
            return {"count": 1, "results": [{"id": 24493}]}

    monkeypatch.setattr("bacdive_cli.core.BacdiveClient", lambda **_: StubClient())

    code = main(["fetch", "24493"])

    assert code == 0
    assert json.loads(capsys.readouterr().out) == {"count": 1, "results": [{"id": 24493}]}


def test_docs_command_outputs_json(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["docs", "fetch", "--format", "json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "bacdive_cli_endpoint_docs"
    assert payload["endpoints"][0]["command"] == "fetch"


def test_parser_reads_cache_defaults_from_xdg_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_path = tmp_path / "bacdive-cli" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '[cache]\nmax_size_gb = 0.5\ndir = "/tmp/bacdive-cache"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    args = build_parser().parse_args(["fetch", "24493"])

    assert args.max_cache_size_gb == 0.5
    assert args.cache_dir == Path("/tmp/bacdive-cache")


def test_main_skips_disk_cache_when_default_cache_is_disabled(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class StubClient:
        def __enter__(self) -> StubClient:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def fetch(self, *_: object, **__: object) -> dict[str, object]:
            return {"count": 1}

    def fail_disk_cache(*_: object, **__: object) -> object:
        raise AssertionError("DiskLRUCache should not be created when cache is disabled")

    monkeypatch.setattr("bacdive_cli.core.BacdiveClient", lambda **_: StubClient())
    monkeypatch.setattr("bacdive_cli.core.DiskLRUCache", fail_disk_cache)

    code = main(["fetch", "24493"])

    assert code == 0
    assert json.loads(capsys.readouterr().out) == {"count": 1}
