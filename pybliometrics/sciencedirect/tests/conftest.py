"""Skip ScienceDirect integration tests if no API key is set."""

import os

import pytest

from pybliometrics.sciencedirect import init

API_KEY = os.getenv("PYBLIOMETRICS_API_KEY")
if not API_KEY:
    pytest.skip("ScienceDirect API not available", allow_module_level=True)
else:
    init(keys=[API_KEY])
