"""The ScienceDirect module."""

from __future__ import annotations

from pathlib import Path

from pybliometrics.sciencedirect.article_entitlement import ArticleEntitlement
from pybliometrics.sciencedirect.article_metadata import ArticleMetadata
from pybliometrics.sciencedirect.article_retrieval import ArticleRetrieval
from pybliometrics.sciencedirect.nonserial_title import NonserialTitle
from pybliometrics.sciencedirect.object_metadata import ObjectMetadata
from pybliometrics.sciencedirect.object_retrieval import ObjectRetrieval
from pybliometrics.sciencedirect.sciencedirect_search import ScienceDirectSearch
from pybliometrics.sciencedirect.subject_classifications import (
    SubjectClassifications as ScDirSubjectClassifications,
)
from pybliometrics.scopus.serial_title import SerialTitle
from pybliometrics.utils import (
    VIEWS,
    chained_get,
    check_field_consistency,
    check_integrity,
    check_parameter_value,
    deduplicate,
    detect_id_type,
    list_authors,
    make_bool_if_possible,
    make_int_if_possible,
    make_search_summary,
    parse_pages,
)
from pybliometrics.utils.startup import init as _init


def init(
    config_path: str | Path | None = None,
    *,
    keys: list[str] | None = None,
    inst_tokens: list[str] | None = None,
    config_dir: str | Path | None = None,
) -> None:
    """Initialize pybliometrics for ScienceDirect usage."""
    _init(
        config_path=config_path,
        keys=keys if keys is not None else ["DUMMY_KEY"],
        inst_tokens=inst_tokens or [],
        config_dir=config_dir,
    )

__all__ = [
    "ArticleEntitlement",
    "ArticleMetadata",
    "ArticleRetrieval",
    "NonserialTitle",
    "ObjectMetadata",
    "ObjectRetrieval",
    "ScDirSubjectClassifications",
    "ScienceDirectSearch",
    "SerialTitle",
    "init",
]
