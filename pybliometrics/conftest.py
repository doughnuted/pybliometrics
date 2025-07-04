"""Test configuration for Pybliometrics."""

import os
from collections.abc import Iterable
from pathlib import Path

import pytest


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: Iterable[pytest.Item]
) -> None:
    """Skip network tests when no API key is provided."""
    if os.getenv("PYBLIOMETRICS_API_KEY"):
        return

    _ = session, config

    skip_reason = "PYBLIOMETRICS_API_KEY not set; skipping network-dependent tests"
    skip_network = pytest.mark.skip(reason=skip_reason)
    for item in items:
        path = str(item.fspath)
        if "scopus/tests" in path or "sciencedirect/tests" in path:
            item.add_marker(skip_network)


def pytest_ignore_collect(path: Path, config: pytest.Config) -> bool:
    """Avoid importing network-dependent tests without an API key."""
    if os.getenv("PYBLIOMETRICS_API_KEY"):
        return False

    _ = config
    path_str = str(path)
    return "scopus/tests" in path_str or "sciencedirect/tests" in path_str
