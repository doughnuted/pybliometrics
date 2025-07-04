"""The ScienceDirect module."""

from pybliometrics.sciencedirect.article_entitlement import ArticleEntitlement
from pybliometrics.sciencedirect.article_metadata import ArticleMetadata
from pybliometrics.sciencedirect.article_retrieval import ArticleRetrieval
from pybliometrics.sciencedirect.nonserial_title import NonserialTitle
from pybliometrics.sciencedirect.object_metadata import ObjectMetadata
from pybliometrics.sciencedirect.object_retrieval import ObjectRetrieval
from pybliometrics.sciencedirect.sciencedirect_search import ScienceDirectSearch
from pybliometrics.sciencedirect.subject_classifications import SubjectClassifications
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
from pybliometrics.utils.startup import init

# alias kept for backward compatibility
ScDirSubjectClassifications = SubjectClassifications

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
    "SubjectClassifications",
    "init",
]
