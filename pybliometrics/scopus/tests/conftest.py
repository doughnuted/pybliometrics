"""Skip Scopus integration tests if no API key is set."""

import os

import pytest

from pybliometrics.scopus import init

API_KEY = os.getenv("PYBLIOMETRICS_API_KEY")
if not API_KEY:
    pytest.skip("Scopus API not available", allow_module_level=True)
else:
    init(keys=[API_KEY])
