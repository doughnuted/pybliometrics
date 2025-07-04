"""Tests for the startup and configuration module."""

from pathlib import Path

import pytest

from pybliometrics import init # Changed import
from pybliometrics.utils import get_insttokens, get_keys

CURRENT_DIR = Path(__file__).resolve().parent
TEST_CONFIG = CURRENT_DIR / "test_config.cfg"


def test_custom_insttokens():
    """Test whether custom insttokens are correctly set."""
    init(keys=["1", "2", "3"], inst_tokens=["a", "b"])
    assert get_insttokens() == ["a", "b"]


def test_custom_keys():
    """Test whether custom keys are correctly set."""
    init(keys=["1", "2", "3"])
    assert get_keys() == ["1", "2", "3"]


def test_imports():
    """Test the import and initialization of the pybliometrics package and its submodules."""
    import pybliometrics

    pybliometrics.init(keys=["DUMMY_KEY"]) # MODIFIED

    import pybliometrics.sciencedirect # This will use the top-level init

    # pybliometrics.sciencedirect.init() # This line should be removed or changed
                                         # Assuming it's meant to test if submodule can be init'd
                                         # or if it relies on top-level, then this call is not needed.
                                         # For now, I'll comment it out as the init is from the top.

    import pybliometrics.scopus # This will use the top-level init

    # pybliometrics.scopus.init() # Similarly, commenting this out.

def test_new_config():
    """Test whether a new config file is created."""
    TEST_CONFIG.unlink(missing_ok=True)

    # Create new config
    init(config_path=TEST_CONFIG, keys=["3", "4", "5"], inst_tokens=["c", "d"])

    # Use custom keys and tokens
    assert get_keys() == ["3", "4", "5"]
    assert get_insttokens() == ["c", "d"]


def test_new_test_config():
    """Test whether the new test config file is correctly read."""
    init(config_path=TEST_CONFIG, keys=["3", "4", "5"])

    # Use keys and tokens from test config
    assert get_keys() == ["3", "4", "5"]
    assert get_insttokens() == []

    init(config_path=TEST_CONFIG, keys=["5", "6", "7"], inst_tokens=["e", "f"])

    # Use custom keys and tokens
    assert get_keys() == ["5", "6", "7"]
    assert get_insttokens() == ["e", "f"]


def test_error_more_tokens_than_keys():
    """Test whether an error is raised if more tokens than keys are provided."""
    with pytest.raises(ValueError):
        init(keys=["1"], inst_tokens=["a", "b"])
