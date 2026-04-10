from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = ["BacdiveClient", "BacdiveCliError"]

if TYPE_CHECKING:
    from .client import BacdiveClient, BacdiveCliError


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .client import BacdiveClient, BacdiveCliError

        exports = {
            "BacdiveClient": BacdiveClient,
            "BacdiveCliError": BacdiveCliError,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
