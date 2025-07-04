import importlib
import sys
from importlib import metadata
from unittest import mock


def test_version_fallback():
    """Package reports fallback version when metadata is missing."""
    sys.modules.pop("pybliometrics", None)
    with mock.patch("importlib.metadata.version", side_effect=metadata.PackageNotFoundError):
        module = importlib.import_module("pybliometrics")
        assert module.__version__ == "0.0.0"
    sys.modules.pop("pybliometrics", None)
    importlib.import_module("pybliometrics")
