"""Top-level package for pybliometrics."""

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - fallback when package isn't installed
    __version__ = version("pybliometrics")
except PackageNotFoundError:  # pragma: no cover - only during tests
    __version__ = "0+unknown"

__citation__ = (
    'Rose, Michael E. and John R. Kitchin: "pybliometrics: '
    'Scriptable bibliometrics using a Python interface to Scopus", SoftwareX '
    "10 (2019) 100263."
)

import pybliometrics.sciencedirect
import pybliometrics.scopus
from pybliometrics.utils.startup import init

__all__ = ["init", "sciencedirect", "scopus"]
