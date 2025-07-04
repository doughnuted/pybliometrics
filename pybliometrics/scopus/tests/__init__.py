# ruff: noqa: E402
"""Tests for pybliometrics.scopus."""

from __future__ import annotations

import os

import pytest

API_KEY = os.getenv("PYBLIOMETRICS_API_KEY")
if not API_KEY:
    pytest.skip(
        "PYBLIOMETRICS_API_KEY not set; skipping network tests",
        allow_module_level=True,
    )

from pybliometrics.scopus import init

init(keys=[API_KEY])
