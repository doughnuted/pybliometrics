"""Utility helpers for parsing Scopus API responses."""

from __future__ import annotations

import contextlib
from collections import namedtuple
from functools import reduce
from html import unescape
from warnings import warn


def filter_digits(text: str) -> str:
    """Return only the digit characters from ``text``."""
    return "".join(filter(str.isdigit, text))


def chained_get(
    container: dict,
    path: list | tuple,
    default: object | None = None,
) -> object | None:
    """Return nested value from ``container`` or ``default`` if missing."""
    # Obtain value via reduce
    try:
        return reduce(lambda c, k: c.get(k, default), path, container)
    except (AttributeError, TypeError):
        return default


def check_integrity(tuples: list, fields: list[str], action: str) -> None:
    """Ensure all `fields` are present in ``tuples`` and act accordingly."""
    for field in fields:
        elements = [getattr(e, field) for e in tuples]
        if None not in elements:
            continue
        msg = (
            "Parsed information doesn't pass integrity check because of "
            f"incomplete information in field '{field}'"
        )
        if action == "raise":
            raise AttributeError(msg)
        if action == "warn":
            warn(msg, stacklevel=2)


def check_field_consistency(needles: list[str], haystack: str) -> None:
    """Raise :class:`ValueError` if items of ``needles`` are missing in ``haystack``."""
    wrong = set(needles) - set(haystack.split())
    if wrong:
        msg = (
            f"Element(s) '{', '.join(sorted(wrong))}' not allowed in "
            "parameter integrity_fields"
        )
        raise ValueError(msg)


def deduplicate(lst: list) -> list:
    """Return ``lst`` without duplicates while preserving order."""
    return reduce(
        lambda acc, item: [*acc, item] if item not in acc else acc,
        lst,
        [],
    )


def get_and_aggregate_subjects(fields: list[dict]) -> dict[str, int]:
    """Aggregate subject areas from Scopus AuthorSearch results."""
    frequencies: dict[str, int] = {}
    for field in fields:
        abbrev = field.get("@abbrev", "")
        freq_str = field.get("@frequency", "")
        frequency = int(freq_str) if freq_str.isdigit() else 0
        if abbrev in frequencies:
            frequencies[abbrev] += frequency
        else:
            frequencies[abbrev] = frequency
    return frequencies


def get_id(s: dict, *, integer: bool = True) -> int | str | None:
    """Return the Scopus ID from ``s``."""
    path = ["coredata", "dc:identifier"]
    try:
        identifier = chained_get(s, path, "").split(":")[-1]
        return int(identifier) if integer else identifier
    except ValueError:
        return None


def get_freetoread(item: dict, path: list[str]) -> str:
    """Return freetoread information from a search result."""
    text = chained_get(item, path)
    with contextlib.suppress(TypeError):
        text = " ".join(x["$"] for x in text)
    return text


def get_link(dct: dict, idx: int, path: list[str] | None = None) -> str | None:
    """Return the link at position ``idx`` from ``dct``."""
    if path is None:
        path = ["coredata", "link"]
    links = chained_get(dct, path, [{}])
    try:
        return links[idx].get("@href")
    except IndexError:
        return None


def html_unescape(text: str) -> str | None:
    """Convert HTML entities in ``text`` to Unicode characters."""
    return unescape(text) if text else None


def listify(element: object) -> list:
    """Return ``element`` as a list if it is not already one."""
    if isinstance(element, list):
        return element
    return [element]


def list_authors(lst: list) -> str:
    """Format a list of authors as 'Firstname Surname'."""
    authors = ", ".join(" ".join([a.given_name, a.surname]) for a in lst[:-1])
    authors += " and " + " ".join([lst[-1].given_name, lst[-1].surname])
    return authors


def make_float_if_possible(val: object) -> float | object:
    """Attempt to convert ``val`` to ``float`` if possible."""
    try:
        return float(val)
    except TypeError:
        return val


def make_int_if_possible(val: object) -> int | object:
    """Attempt to convert ``val`` to ``int`` if possible."""
    try:
        return int(val)
    except TypeError:
        return val


def make_bool_if_possible(val: object) -> bool | object:
    """Attempt to convert ``val`` to ``bool`` if possible."""
    if isinstance(val, str):
        return val.lower() == "true"
    if isinstance(val, int):
        return bool(val)
    return val


def make_search_summary(
    self: object,
    keyword: str,
    results: list[str] | None,
    joiner: str = "\n    ",
) -> str:
    """Return a summary string for search classes."""
    date = self.get_cache_file_mdate().split()[0]
    if self._n != 1:
        appendix = "s"
        verb = "have"
    else:
        appendix = ""
        verb = "has"
    s = f"Search '{self._query}' yielded {self._n:,} {keyword}{appendix} as of {date}"
    if results:
        s += ":" + joiner + joiner.join(results)
    elif self._n:
        s += f", which {verb} not been downloaded"
    return s


def parse_affiliation(affs: dict | list, view: str) -> list | None:
    """Parse a list of affiliation-related information."""
    order = (
        "id parent type relationship afdispname preferred_name "
        "parent_preferred_name country_code country address_part city "
        "state postal_code org_domain org_URL"
    )
    aff = namedtuple("Affiliation", order, defaults=(None,) * len(order.split()))
    out = []

    if view in ("STANDARD", "ENHANCED"):
        for item in listify(affs):
            if not item:
                continue
            doc = item.get("ip-doc", {}) or {}
            address = doc.get("address", {}) or {}
            try:
                parent = int(item["@parent"])
            except KeyError:
                parent = None
            new = aff(
                id=int(item["@affiliation-id"]),
                parent=parent,
                type=doc.get("@type"),
                relationship=doc.get("@relationship"),
                afdispname=doc.get("@afdispname"),
                preferred_name=doc.get("preferred-name", {}).get("$"),
                parent_preferred_name=doc.get("parent-preferred-name", {}).get("$"),
                country_code=address.get("@country"),
                country=address.get("country"),
                address_part=address.get("address-part"),
                city=address.get("city"),
                postal_code=address.get("postal-code"),
                state=address.get("state"),
                org_domain=doc.get("org-domain"),
                org_URL=doc.get("org-URL"),
            )
            if any(val for val in new):
                out.append(new)
    elif view == "LIGHT":
        new = aff(
            preferred_name=affs.get("affiliation-name"),
            city=affs.get("affiliation-city"),
            country=affs.get("affiliation-country"),
        )
        if any(val for val in new):
            out.append(new)

    return out or None


def parse_date_created(dct: dict) -> tuple[int | None, int | None, int | None]:
    """Return year, month and day from ``dct`` if available."""
    date = dct.get("date-created")
    if date:
        return int(date["@year"]), int(date["@month"]), int(date["@day"])
    return None, None, None


def parse_pages(self: object, *, unicode: bool = False) -> str:
    """Return formatted page range of a document."""
    if self.pageRange:
        pages = f"pp. {self.pageRange}"
    elif self.startingPage:
        pages = f"pp. {self.startingPage}-{self.endingPage}"
    else:
        pages = "(no pages found)"
    if unicode:
        pages = f"{pages}"
    return pages
