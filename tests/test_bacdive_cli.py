from __future__ import annotations

import json

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
