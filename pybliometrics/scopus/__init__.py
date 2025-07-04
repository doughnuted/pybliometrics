"""The scopus module contains classes to access Scopus APIs."""

from __future__ import annotations

from pathlib import Path

from pybliometrics.scopus.abstract_citation import (
    CitationOverview,
    _maybe_return_list,
    _parse_dict,
)
from pybliometrics.scopus.abstract_retrieval import (
    AbstractRetrieval,
    _get_org,
    _list_authors,
    _parse_pages,
    _select_by_idtype,
)
from pybliometrics.scopus.affiliation_retrieval import AffiliationRetrieval
from pybliometrics.scopus.affiliation_search import AffiliationSearch
from pybliometrics.scopus.author_retrieval import AuthorRetrieval
from pybliometrics.scopus.author_search import AuthorSearch
from pybliometrics.scopus.plumx_metrics import PlumXMetrics, _format_as_namedtuple_list
from pybliometrics.scopus.scopus_search import ScopusSearch, _join, _replace_none
from pybliometrics.scopus.serial_search import (
    SerialSearch,
    _merge_subject_data,
    _retrieve_cite_scores,
    _retrieve_links,
    _retrieve_source_rankings,
    _retrieve_yearly_data,
)
from pybliometrics.scopus.serial_title import (
    SerialTitle,
    _get_all_cite_score_years,
    _parse_list,
)
from pybliometrics.scopus.subject_classifications import SubjectClassifications
from pybliometrics.utils import (
    VIEWS,
    chained_get,
    check_field_consistency,
    check_integrity,
    check_parameter_value,
    deduplicate,
    detect_id_type,
    filter_digits,
    get_and_aggregate_subjects,
    get_content,
    get_id,
    get_link,
    html_unescape,
    listify,
    make_int_if_possible,
    make_search_summary,
    parse_date_created,
)
from pybliometrics.utils.startup import init as _init


def init(
    config_path: str | Path | None = None,
    *,
    keys: list[str] | None = None,
    inst_tokens: list[str] | None = None,
    config_dir: str | Path | None = None,
) -> None:
    """Initialize pybliometrics for Scopus usage."""
    _init(
        config_path=config_path,
        keys=keys if keys is not None else ["DUMMY_KEY"],
        inst_tokens=inst_tokens or [],
        config_dir=config_dir,
    )

__all__ = [
    "AbstractRetrieval",
    "AffiliationRetrieval",
    "AffiliationSearch",
    "AuthorRetrieval",
    "AuthorSearch",
    "CitationOverview",
    "PlumXMetrics",
    "ScopusSearch",
    "SerialSearch",
    "SerialTitle",
    "SubjectClassifications",
    "init",
]
