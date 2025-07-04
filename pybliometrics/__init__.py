from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pybliometrics")
except PackageNotFoundError:  # pragma: no cover - executed when package metadata is missing
    __version__ = "0.0.0"

__citation__ = (
    'Rose, Michael E. and John R. Kitchin: "pybliometrics: '
    'Scriptable bibliometrics using a Python interface to Scopus", SoftwareX '
    "10 (2019) 100263."
)

import pybliometrics.sciencedirect
import pybliometrics.scopus
from pybliometrics.utils.startup import init

__all__ = ["init", "sciencedirect", "scopus"]
