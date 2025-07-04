"""Module for Scopus Abstract Retrieval API."""

from __future__ import annotations

from collections import defaultdict, namedtuple
from typing import Optional, Union  # Re-added Optional

from pybliometrics.superclasses import Retrieval
from pybliometrics.utils import (
    VIEWS,
    chained_get,
    check_parameter_value,
    deduplicate,
    detect_id_type,
    get_id,
    get_link,
    listify,
    make_int_if_possible,
    parse_date_created,
)


class AbstractRetrieval(Retrieval):
    """
    Class to retrieve a Scopus abstract.

    Notes
    -----
    The Scopus Abstract Retrieval API covers all Scopus documents.
    For more information, see https://dev.elsevier.com/documentation/AbstractRetrievalAPI.wadl.

    For a list of fields that can be downloaded, see
    https://dev.elsevier.com/sc_abstract_retrieval_views.html.
    Not all fields are available for all documents.

    """

    @property
    def abstract(self) -> str | None:
        """
        The abstract of a document.

        Note: If this is empty, try `description` property instead.
        """
        return self._head.get("abstracts")

    @property
    def affiliation(self) -> list[namedtuple] | None:
        """
        A list of namedtuples representing listed affiliations.

        The form is `(id, name, city, country)`.
        """
        out = []
        aff = namedtuple("Affiliation", "id name city country")
        affs = listify(self._json.get("affiliation", []))
        for item in affs:
            new = aff(
                id=make_int_if_possible(item.get("@id")),
                name=item.get("affilname"),
                city=item.get("affiliation-city"),
                country=item.get("affiliation-country"),
            )
            out.append(new)
        return out or None

    @property
    def aggregation_type(self) -> str:
        """Return the aggregation type of source the document is published in."""
        return chained_get(self._json, ["coredata", "prism:aggregationType"])

    @property
    def authkeywords(self) -> list[str] | None:
        """Return a list of author-provided keywords of the document."""
        keywords = self._json.get("authkeywords")
        if not keywords:
            return None
        try:
            return [d["$"] for d in keywords["author-keyword"]]
        except TypeError:  # Singleton keyword
            return [keywords["author-keyword"]["$"]]

    @property
    def authorgroup(self) -> list[namedtuple] | None:
        """
        A list of namedtuples representing the article's authors and collaborations.

        Organized by affiliation, in the form:
        `(affiliation_id, collaboration_id, dptid, organization, city, postalcode,
        addresspart, country, auid, orcid, indexed_name, surname, given_name)`.

        If `given_name` is not present, fall back to initials.

        Note: Affiliation information might be missing or mal-assigned even
        when it looks correct in the web view.  In this case please request
        a correction.  It is generally missing for collaborations.
        """
        # Information can be one of three forms:
        # 1. A dict with one key (author) or two keys (affiliation and author)
        # 2. A list of dicts with as in 1, one for each affiliation (incl. missing)
        # 3. A list of two dicts with one key each (author and collaboration)
        # Initialization
        fields = (
            "affiliation_id collaboration_id dptid organization city postalcode "
            "addresspart country auid orcid indexed_name surname given_name"
        )
        auth = namedtuple("Author", fields, defaults=[None for _ in fields.split()])
        items = listify(self._head.get("author-group", []))
        out = []
        for item in filter(None, items):
            # Get all possible items: affiliation, author, collaboration
            aff = item.get("affiliation", {})
            authors = item.get("author", [])
            collaborations = item.get("collaboration", {})
            # Affiliation information
            aff_id = make_int_if_possible(aff.get("@afid"))
            dep_id = make_int_if_possible(aff.get("@dptid"))
            org = _get_org(aff)
            # Author information
            for author in authors:
                new = auth(
                    affiliation_id=aff_id,
                    organization=org,
                    city=aff.get("city"),
                    dptid=dep_id,
                    postalcode=aff.get("postal-code"),
                    addresspart=aff.get("address-part"),
                    country=aff.get("country"),
                    auid=make_int_if_possible(author.get("@auid")),
                    orcid=author.get("@orcid"),
                    surname=author.get("ce:surname"),
                    given_name=author.get("ce:given-name", author.get("ce:initials")),
                    indexed_name=chained_get(
                        author, ["preferred-name", "ce:indexed-name"]
                    ),
                )
                out.append(new)
            # Collaboration information
            for collaboration in filter(None, listify(collaborations)):
                new = auth(
                    collaboration_id=collaboration.get("@collaboration-instance-id"),
                    indexed_name=collaboration.get("ce:indexed-name"),
                )
                out.append(new)
        return out or None

    @property
    def authors(self) -> list[namedtuple] | None:
        """
        A list of namedtuples representing the article's authors.

        The form is `(auid, indexed_name, surname, given_name, affiliation)`.
        In case multiple affiliation IDs are given, they are joined on `";"`.

        Note: The affiliation referred to here is what Scopus' algorithm
        determined as the main affiliation.  Property `authorgroup` provides
        all affiliations.
        """
        out = []
        fields = "auid indexed_name surname given_name affiliation"
        auth = namedtuple("Author", fields)
        for item in chained_get(self._json, ["authors", "author"], []):
            affs = [a for a in listify(item.get("affiliation")) if a] or None
            try:
                aff = ";".join([aff.get("@id") for aff in affs])
            except TypeError:
                aff = None
            new = auth(
                auid=int(item["@auid"]),
                surname=item.get("ce:surname"),
                indexed_name=item.get("ce:indexed-name"),
                affiliation=aff,
                given_name=chained_get(item, ["preferred-name", "ce:given-name"]),
            )
            out.append(new)
        return out or None

    @property
    def citedby_count(self) -> int | None:
        """Return the number of articles citing the document."""
        path = ["coredata", "citedby-count"]
        return make_int_if_possible(chained_get(self._json, path))

    @property
    def citedby_link(self) -> str:
        """Return the URL to Scopus page listing citing documents."""
        return get_link(self._json, 2)

    @property
    def chemicals(self) -> list[namedtuple] | None:
        """
        Return a list of namedtuples representing chemical entities.

        The form is `(source, chemical_name, cas_registry_number)`.
        In case multiple numbers given, they are joined on `";"`.
        """
        path = ["enhancement", "chemicalgroup", "chemicals"]
        items = listify(chained_get(self._head, path, []))
        fields = "source chemical_name cas_registry_number"
        chemical = namedtuple("Chemical", fields)
        out = []
        for item in items:
            for chem in listify(item["chemical"]):
                number = chem.get("cas-registry-number")
                try:  # Multiple numbers given
                    num = ";".join([n["$"] for n in number])
                except TypeError:
                    num = number
                new = chemical(
                    source=item["@source"],
                    cas_registry_number=num,
                    chemical_name=chem["chemical-name"],
                )
                out.append(new)
        return out or None

    @property
    def confcode(self) -> int | None:
        """Return the code of the conference the document belongs to."""
        return make_int_if_possible(self._confevent.get("confcode"))

    @property
    def confdate(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """
        Return the date range of the conference the document belongs to.

        Represented by two tuples in the form (YYYY, MM, DD).
        """
        dates = self._confevent.get("confdate", {})
        try:
            keys = ("startdate", "enddate")
            date_order = ("@year", "@month", "@day")
            d = (tuple(int(dates[k1][k2]) for k2 in date_order) for k1 in keys)
            return tuple(d)
        except KeyError:
            return None

    @property
    def conflocation(self) -> str | None:
        """Return the location of the conference the document belongs to."""
        return chained_get(self._confevent, ["conflocation", "city-group"])

    @property
    def confname(self) -> str | None:
        """Return the name of the conference the document belongs to."""
        return self._confevent.get("confname")

    @property
    def confsponsor(self) -> list[str] | str | None:
        """Return the sponsor(s) of the conference the document belongs to."""
        path = ["confsponsors", "confsponsor"]
        sponsors = chained_get(self._confevent, path, [])
        if len(sponsors) == 0:
            return None
        if isinstance(sponsors, list):
            return [s["$"] for s in sponsors]
        return sponsors

    @property
    def contributor_group(self) -> list[namedtuple] | None:
        """
        Return a list of namedtuples representing contributors compiled by Scopus.

        The form is `(given_name, initials, surname, indexed_name, role)`.
        """
        path = ["source", "contributor-group"]
        items = listify(chained_get(self._head, path, []))
        out = []
        fields = "given_name initials surname indexed_name role"
        pers = namedtuple("Contributor", fields)
        for item in items:
            entry = item.get("contributor", {})
            new = pers(
                given_name=entry.get("ce:given-name"),
                initials=entry.get("ce:initials"),
                surname=entry.get("ce:surname"),
                indexed_name=entry.get("ce:indexed-name"),
                role=entry.get("@role"),
            )
            out.append(new)
        return out or None

    @property
    def copyright(self) -> str:
        """Return the copyright statement of the document."""
        path = ["item", "bibrecord", "item-info", "copyright", "$"]
        return chained_get(self._json, path)

    @property
    def copyright_type(self) -> str:
        """Return the copyright holder of the document."""
        path = ["item", "bibrecord", "item-info", "copyright", "@type"]
        return chained_get(self._json, path)

    @property
    def correspondence(self) -> list[namedtuple] | None:
        """
        Return a list of namedtuples representing the authors for correspondence.

        The form is `(surname, initials, organization, country, city_group)`.
        Multiple organizations are joined on semicolon.
        """
        fields = "surname initials organization country city_group"
        auth = namedtuple("Correspondence", fields)
        items = listify(self._head.get("correspondence", []))
        out = []
        for item in items:
            aff = item.get("affiliation", {})
            try:
                org = aff["organization"]
                try:
                    org = org["$"]
                except TypeError:  # Multiple names given
                    org = "; ".join([d["$"] for d in org])
            except KeyError:
                org = None
            new = auth(
                surname=item.get("person", {}).get("ce:surname"),
                initials=item.get("person", {}).get("ce:initials"),
                organization=org,
                country=aff.get("country"),
                city_group=aff.get("city-group"),
            )
            out.append(new)
        return out or None

    @property
    def cover_date(self) -> str:
        """Return the date of the cover the document is in."""
        return chained_get(self._json, ["coredata", "prism:coverDate"])

    @property
    def date_created(self) -> tuple[int, int, int] | None:
        """Return the `date_created` of a record."""
        path = ["item", "bibrecord", "item-info", "history"]
        d = chained_get(self._json, path, {})
        try:
            return parse_date_created(d)
        except KeyError:
            return None

    @property
    def description(self) -> str | None:
        """
        Return the description of a record.

        Note: If this is empty, try `abstract` property instead.
        """
        return chained_get(self._json, ["coredata", "dc:description"])

    @property
    def document_entitlement_status(self) -> str | None:
        """
        Return the document entitlement status.

        i.e. tells if the requestor is entitled to the requested resource.

        Note: Only works with `ENTITLED` view.
        """
        return chained_get(self._json, ["document-entitlement", "status"])

    @property
    def doi(self) -> str | None:
        """Return the DOI of the document."""
        return chained_get(self._json, ["coredata", "prism:doi"])

    @property
    def eid(self) -> str:
        """Return the EID of the document."""
        return chained_get(self._json, ["coredata", "eid"])

    @property
    def ending_page(self) -> str | None:
        """
        Return the ending page.

        If this is empty, try `pageRange` property instead.
        """
        # Try coredata first, fall back to head afterwards
        ending = chained_get(self._json, ["coredata", "prism:endingPage"])
        if ending:
            return ending
        path = ["source", "volisspag", "pagerange", "@last"]
        return chained_get(self._head, path)

    @property
    def funding(self) -> list[namedtuple] | None:
        """
        Return a list of namedtuples parsed funding information.

        The form is `(agency, agency_id, string, funding_id, acronym, country)`.
        """

        def _get_funding_id(f_dict: dict) -> list:
            funding_get = f_dict.get("xocs:funding-id", [])
            try:
                return [v["$"] for v in funding_get] or None  # multiple or empty
            except TypeError:
                return [funding_get]  # single

        path = ["item", "xocs:meta", "xocs:funding-list", "xocs:funding"]
        funds = listify(chained_get(self._json, path, []))
        out = []
        fields = "agency agency_id string funding_id acronym country"
        fund = namedtuple("Funding", fields)
        for item in funds:
            new = fund(
                agency=item.get("xocs:funding-agency"),
                agency_id=item.get("xocs:funding-agency-id"),
                string=item.get("xocs:funding-agency-matched-string"),
                funding_id=_get_funding_id(item),
                acronym=item.get("xocs:funding-agency-acronym"),
                country=item.get("xocs:funding-agency-country"),
            )
            out.append(new)
        return out or None

    @property
    def funding_text(self) -> str | None:
        """Return the raw text from which Scopus derives funding information."""
        path = ["item", "xocs:meta", "xocs:funding-list", "xocs:funding-text"]
        return chained_get(self._json, path)

    @property
    def isbn(self) -> tuple[str, ...] | None:
        """
        Return ISBNs to publicationName as tuple of varying length.

        (e.g. ISBN-10 or ISBN-13).
        """
        isbns = listify(chained_get(self._head, ["source", "isbn"], []))
        if len(isbns) == 0:
            return None
        return tuple(i["$"] for i in isbns)

    @property
    def issn(self) -> namedtuple | None:
        """
        Return a namedtuple in the form `(print electronic)`.

        Note: If the source has an E-ISSN, the META view will return None.
        Use FULL view instead.
        """
        container = defaultdict(lambda: None)
        # Parse information from head (from FULL view)
        info = listify(chained_get(self._head, ["source", "issn"], []))
        for t in info:
            try:
                container[t["@type"]] = t["$"]
            except TypeError:
                container["print"] = t
        # Parse information from coredata as fallback
        fallback = chained_get(self._json, ["coredata", "prism:issn"])
        if fallback and len(container) < 2:  # PLR2004: Magic value 2
            parts = fallback.split()
            if len(parts) == 2:  # PLR2004: Magic value 2
                if len(container) == 1:
                    for n, o in (("electronic", "print"), ("print", "electronic")):
                        if n not in container:
                            container[n] = [p for p in parts if p != container[o]]
                else:
                    # no way to find out which is which
                    pass
            else:
                container["print"] = parts[0]
        # Finalize
        issns = namedtuple("ISSN", "print electronic", defaults=(None, None))
        if not container:
            return None
        return issns(**container)

    @property
    def identifier(self) -> int:
        """Return the ID of the document (same as EID without "2-s2.0-")."""
        return get_id(self._json)

    @property
    def idxterms(self) -> list[str] | None:
        """
        Return a list of index terms.

        These are just one category of those Scopus provides in the web version.
        """
        try:
            terms = listify(self._json.get("idxterms", {}).get("mainterm", []))
        except AttributeError:  # idxterms is empty
            return None
        try:
            return [d["$"] for d in terms] or None
        except AttributeError:
            return None

    @property
    def issue_identifier(self) -> str | None:
        """Return the number of the issue the document was published in."""
        return chained_get(self._json, ["coredata", "prism:issueIdentifier"])

    @property
    def issuetitle(self) -> str | None:
        """Return the title of the issue the document was published in."""
        return chained_get(self._head, ["source", "issuetitle"])

    @property
    def language(self) -> str | None:
        """Return the language of the article."""
        return chained_get(self._json, ["language", "@xml:lang"])

    @property
    def openaccess(self) -> int | None:
        """Return the openaccess status encoded in single digits."""
        path = ["coredata", "openaccess"]
        return make_int_if_possible(chained_get(self._json, path))

    @property
    def openaccess_flag(self) -> bool | None:
        """Return whether the document is available via open access or not."""
        flag = chained_get(self._json, ["coredata", "openaccessFlag"])
        if flag:
            flag = flag == "true"
        return flag

    @property
    def page_range(self) -> str | None:
        """
        Return the page range.

        If this is empty, try `startingPage` and
        `endingPage` properties instead.
        """
        # Try data from coredata first, fall back to head afterwards
        pages = chained_get(self._json, ["coredata", "prism:pageRange"])
        if not pages:
            return chained_get(self._head, ["source", "volisspag", "pages"])
        return pages

    @property
    def pii(self) -> str | None:
        """Return the PII (Publisher Item Identifier) of the document."""
        return chained_get(self._json, ["coredata", "pii"])

    @property
    def publication_name(self) -> str | None:
        """Return the name of source the document is published in."""
        return chained_get(self._json, ["coredata", "prism:publicationName"])

    @property
    def publisher(self) -> str | None:
        """
        Return the name of the publisher of the document.

        Note: Information provided in the FULL view of the article might be
        more complete.
        """
        # Return information from FULL view, fall back to other views
        full = chained_get(self._head, ["source", "publisher", "publishername"])
        if full is None:
            return chained_get(self._json, ["coredata", "dc:publisher"])
        return full

    @property
    def publisher_address(self) -> str | None:
        """Return the address of the publisher of the document."""
        return chained_get(self._head, ["source", "publisher", "publisheraddress"])

    @property
    def pubmed_id(self) -> int | None:
        """Return the PubMed ID of the document."""
        path = ["coredata", "pubmed-id"]
        return make_int_if_possible(chained_get(self._json, path))

    @property
    def refcount(self) -> int | None:
        """
        Return the number of references of an article.

        Note: Requires either the FULL view or REF view.
        """
        try:  # REF view
            return int(self._ref["@total-references"])
        except KeyError:  # FULL view
            try:
                return int(self._ref["@refcount"])
            except KeyError:
                return None

    @property
    def references(self) -> list[namedtuple] | None:
        """
        Return a list of namedtuples representing references listed in the document.

        The form is:
        `(position, id, doi, title, authors, authors_auid, authors_affiliationid,
        sourcetitle, publicationyear, coverDate, volume, issue, first, last,
        citedbycount, type, text, fulltext)`.

        Fields:
        - `position`: Number at which the reference appears.
        - `id`: Scopus ID of the referenced document (EID without "2-s2.0-").
        - `authors`: String of author names ("Surname1, Initials1; ...").
        - `authors_auid`: String of author IDs, joined by "; ".
        - `authors_affiliationid`: String of author affiliation IDs, joined by "; ".
        - `sourcetitle`: Name of the source (e.g., journal).
        - `publicationyear`: Year of publication (FULL view only).
        - `coverDate`: Date of publication (REF view only).
        - `volume`, `issue`: Volume and issue strings.
        - `first`, `last`: Page range.
        - `citedbycount`: Total citations of the cited item (REF view only).
        - `type`: Parsing status of the reference (resolved or not).
        - `text`: Information on the publication.
        - `fulltext`: Text authors used for the reference.

        Note: Requires either the FULL view or REF view.
        Might be empty even if `refcount` is positive. Specific fields can be empty.
        `authors` and `authors_auid` lists may contain duplicates due to 1:1
        pairing with `authors_affiliationid`.
        """
        out = []
        field_names = (
            "position",
            "id",
            "doi",
            "title",
            "authors",
            "authors_auid",
            "authors_affiliationid",
            "sourcetitle",
            "publicationyear",
            "coverDate",
            "volume",
            "issue",
            "first",
            "last",
            "citedbycount",
            "type",
            "text",
            "fulltext",
        )
        ref = namedtuple("Reference", field_names)
        items = listify(self._ref.get("reference", []))
        for item in items:
            try:
                info = item.get("ref-info", item)
            except AttributeError:  # item not a dictionary
                continue
            volisspag = info.get("volisspag", {}) or {}
            if isinstance(volisspag, list):
                volisspag = volisspag[0]
            volis = volisspag.get("voliss", {})
            if isinstance(volis, list):
                volis = volis[0]
            # Parse author information
            if self._view == "FULL":  # FULL view parsing
                auth = listify(info.get("ref-authors", {}).get("author", []))
                authors = [
                    ", ".join(filter(None, [d.get("ce:surname"), d.get("ce:initials")]))
                    for d in auth
                ]
                auids = None
                affids = None
                ids = listify(info["refd-itemidlist"]["itemid"])
                doi = _select_by_idtype(ids, id_type="DOI")
                scopus_id = _select_by_idtype(ids, id_type="SGR")
            else:  # REF view parsing
                auth = (info.get("author-list") or {}).get("author", [])
                auth = deduplicate(auth)
                authors = [
                    ", ".join(
                        filter(None, [d.get("ce:surname"), d.get("ce:given-name")])
                    )
                    for d in auth
                ]
                auids = "; ".join(filter(None, [d.get("@auid") for d in auth]))
                affs = filter(None, [d.get("affiliation") for d in auth])
                affids = "; ".join([aff.get("@id") for aff in affs])
                doi = info.get("ce:doi")
                scopus_id = info.get("scopus-id")
            # Combine information
            new = ref(
                position=item.get("@id"),
                id=scopus_id,
                doi=doi,
                title=info.get("ref-title", {}).get("ref-titletext", info.get("title")),
                authors="; ".join(authors),
                authors_auid=auids or None,
                authors_affiliationid=affids or None,
                sourcetitle=info.get("ref-sourcetitle", info.get("sourcetitle")),
                publicationyear=info.get("ref-publicationyear", {}).get("@first"),
                coverDate=info.get("prism:coverDate"),
                volume=volis.get("@volume"),
                issue=volis.get("@issue"),
                first=volisspag.get("pagerange", {}).get("@first"),
                last=volisspag.get("pagerange", {}).get("@last"),
                citedbycount=info.get("citedby-count"),
                type=info.get("type"),
                text=info.get("ref-text"),
                fulltext=item.get("ref-fulltext"),
            )
            out.append(new)
        return out or None

    @property
    def scopus_link(self) -> str:
        """Return the URL to the document page on Scopus."""
        return get_link(self._json, 1)

    @property
    def self_link(self) -> str:
        """Return the URL to Scopus API page of this document."""
        return get_link(self._json, 0)

    @property
    def sequencebank(self) -> list[namedtuple] | None:
        """
        Return a list of namedtuples representing biological entities.

        Defined or mentioned in the text, in the form `(name, sequence_number, type)`.
        """
        path = ["enhancement", "sequencebanks", "sequencebank"]
        items = listify(chained_get(self._head, path, []))
        bank = namedtuple("Sequencebank", "name sequence_number type")
        out = []
        for item in items:
            numbers = listify(item["sequence-number"])
            for number in numbers:
                new = bank(
                    name=item["@name"],
                    sequence_number=number["$"],
                    type=number["@type"],
                )
                out.append(new)
        return out or None

    @property
    def source_id(self) -> int | None:
        """Return the Scopus source ID of the document."""
        path = ["coredata", "source-id"]
        return make_int_if_possible(chained_get(self._json, path))

    @property
    def sourcetitle_abbreviation(self) -> str | None:
        """
        Return the abbreviation of the source the document is published in.

        Note: Requires the FULL view of the article.
        """
        return self._head.get("source", {}).get("sourcetitle-abbrev")

    @property
    def srctype(self) -> str | None:
        """
        Return the aggregation type of source the document is published in.

        Short version of aggregationType.
        """
        return chained_get(self._json, ["coredata", "srctype"])

    @property
    def starting_page(self) -> str | None:
        """
        Return the starting page.

        If this is empty, try `pageRange` property instead.
        """
        # Try coredata first, fall back to bibrecord afterwards
        starting = chained_get(self._json, ["coredata", "prism:startingPage"])
        if starting:
            return starting
        path = ["source", "volisspag", "pagerange", "@first"]
        return chained_get(self._head, path)

    @property
    def subject_areas(self) -> list[namedtuple] | None:
        """
        Return a list of namedtuples containing subject areas of the article.

        In the form `(area abbreviation code)`.

        Note: Requires the FULL view of the article.
        """
        area = namedtuple("Area", "area abbreviation code")
        path = ["subject-areas", "subject-area"]
        out = [
            area(area=item["$"], abbreviation=item["@abbrev"], code=int(item["@code"]))
            for item in listify(chained_get(self._json, path, []))
        ]
        return out or None

    @property
    def subtype(self) -> str | None:
        """
        Return the type of the document.

        Refer to the Scopus Content Coverage Guide
        for a list of possible values.  Short version of subtypedescription.
        """
        return chained_get(self._json, ["coredata", "subtype"]) or None

    @property
    def subtype_description(self) -> str | None:
        """
        Return the type of the document.

        Refer to the Scopus Content Coverage Guide
        for a list of possible values.  Long version of subtype.
        """
        return chained_get(self._json, ["coredata", "subtypeDescription"]) or None

    @property
    def title(self) -> str | None:
        """Return the title of the document."""
        return chained_get(self._json, ["coredata", "dc:title"])

    @property
    def url(self) -> str | None:
        """Return the URL to the API view of the document."""
        return chained_get(self._json, ["coredata", "prism:url"])

    @property
    def volume(self) -> str | None:
        """Return the volume for the document."""
        return chained_get(self._json, ["coredata", "prism:volume"])

    @property
    def website(self) -> str | None:
        """Return the website of publisher."""
        path = ["source", "website", "ce:e-address", "$"]
        return chained_get(self._head, path)

    def __init__(
        self,
        identifier: Optional[Union[int, str]] = None,
        *,
        refresh: Union[bool, int] = False,
        view: str = "META_ABS",
        id_type: Optional[str] = None,
        **kwds: str,
    ) -> None:
        """
        Initialize the Abstract Retrieval API interaction.

        :param identifier: The identifier of a document. Can be the Scopus EID,
                           the Scopus ID, the PII, the Pubmed-ID, or the DOI.
        :param refresh: Whether to refresh the cached file if it exists.
                        If an int is passed, the cached file will be refreshed if the
                        number of days since last modification exceeds that value.
        :param id_type: The type of used ID. Allowed values: None, 'eid', 'pii',
                        'scopus_id', 'pubmed_id', 'doi'. If None,
                        the function tries to infer the ID type.
        :param view: The view of the file to download. Allowed values: META,
                     META_ABS, REF, FULL, ENTITLED. FULL includes all
                     information of META_ABS, which includes all of META.
                     For details, see
                     https://dev.elsevier.com/sc_abstract_retrieval_views.html.
                     Note: `ENTITLED` view only contains `document_entitlement_status`.
        :param kwds: Keywords passed as query parameters. Must contain
                     fields and values from the API specification at
                     https://dev.elsevier.com/documentation/AbstractRetrievalAPI.wadl.

        Raises
        ------
        ValueError
            If `id_type`, `refresh`, or `view` is not an allowed value.

        Notes
        -----
        The directory for cached results is `{path}/{view}/{identifier}`,
        where `path` is specified in your configuration file.
        If `identifier` is a DOI, an underscore replaces the forward slash.

        """
        # Checks
        identifier_str = str(identifier) if identifier is not None else None
        check_parameter_value(view, VIEWS["AbstractRetrieval"], "view")
        if id_type is None and identifier_str is not None:
            id_type = detect_id_type(identifier_str)
        elif id_type is not None:
            allowed_id_types = ("eid", "pii", "scopus_id", "pubmed_id", "doi")
            check_parameter_value(id_type, allowed_id_types, "id_type")

        # Load json
        self._view = view
        self._refresh = refresh
        Retrieval.__init__(self, identifier=identifier_str, id_type=id_type, **kwds)
        if self._json and self._view in ("META", "META_ABS", "REF", "FULL"):
            self._json = self._json.get("abstracts-retrieval-response", self._json)
        self._head = chained_get(self._json, ["item", "bibrecord", "head"], {})
        conf_path = ["source", "additional-srcinfo", "conferenceinfo", "confevent"]
        self._confevent = chained_get(self._head, conf_path, {})
        if self._view == "REF":
            ref_path = ["references"]
        else:
            ref_path = ["item", "bibrecord", "tail", "bibliography"]
        self._ref = chained_get(self._json, ref_path, {})

    def __str__(self) -> str:
        """
        Return a pretty text version of the document.

        Assumes the document is a journal article and was loaded with
        view="META_ABS" or view="FULL".
        """

        def convert_citedbycount(entry: namedtuple) -> float:
            """Convert cited-by count to float, return 0.0 on error."""
            try:
                return float(entry.citedbycount) or 0.0
            except (ValueError, TypeError):
                return 0.0

        def get_date_str(cover_date_val: Optional[str]) -> Optional[str]:
            """Extract year from cover date string."""
            try:
                return cover_date_val[:4] if cover_date_val else None
            except TypeError:
                return None

        s = ""
        if self._view in ("FULL", "META_ABS", "META"):
            date_str = self.get_cache_file_mdate().split()[0]
            authors_str = "(No author found)"
            if self.authors:
                if len(self.authors) > 1:
                    authors_str = _list_authors(self.authors)
                elif self.authors:  # Should be len == 1
                    a = self.authors[0]
                    authors_str = f"{a.given_name or ''} {a.surname or ''}".strip()

            title_str = self.title or ""
            pub_name_str = self.publication_name or ""
            volume_str = self.volume or ""

            s_parts = [f'{authors_str}: "{title_str}", {pub_name_str}, {volume_str}']
            if self.issue_identifier:
                s_parts.append(f"({self.issue_identifier})")
            s_parts.append(", ")
            s_parts.append(_parse_pages(self))
            cover_date_year = (self.cover_date or "----")[:4]
            s_parts.append(f"({cover_date_year}).")
            if self.doi:
                s_parts.append(f" https://doi.org/{self.doi}.\n")
            s_parts.append(f"{self.citedby_count or 0} citation(s) as of {date_str}")
            if self.affiliation:
                s_parts.append("\n  Affiliation(s):\n   ")
                s_parts.append(
                    "\n   ".join([aff.name for aff in self.affiliation if aff.name])
                )
            s = "".join(s_parts)

        elif self._view in ("REF",):
            top_n = 5
            top_references = []
            if self.references:
                try:
                    references_list = self.references
                    references_sorted = sorted(
                        references_list, key=convert_citedbycount, reverse=True
                    )
                    top_references = [
                        f"{ref.title or ''} ({get_date_str(ref.coverDate) or 'N/A'}). "
                        f"EID: {ref.id or 'N/A'}"
                        for ref in references_sorted[:top_n]
                    ]
                except TypeError:
                    pass

            s = f"A total of {self.refcount or 0} references were found. "
            if top_n and top_references:
                s += f"Top {top_n} references:\n\t"
                s += "\n\t".join(top_references)
        return s

    def get_bibtex(self) -> str:
        """
        Return the bibliographic entry in BibTeX format.

        Raises
        ------
        ValueError
            If the item's aggregation_type is not "Journal".

        """
        if self.aggregation_type != "Journal":
            error_msg = "Only Journal articles supported."
            raise ValueError(error_msg)

        year = (self.cover_date or "----")[:4]
        authors_list = self.authors or []

        title_str = self.title or "Unknown Title"
        title_parts = title_str.split()

        if not authors_list:
            key_surname = "UnknownAuthor"
        else:
            key_surname = authors_list[0].surname or "Unknown"

        key_title_first = title_parts[0].title() if title_parts else "UnknownFirst"
        key_title_last = title_parts[-1].title() if title_parts else "UnknownLast"

        key = "".join([key_surname, year, key_title_first, key_title_last])

        authors_str = " and ".join(
            [f"{a.given_name or ''} {a.surname or ''}".strip() for a in authors_list]
        )

        if self.page_range:
            pages = self.page_range
        elif self.starting_page and self.ending_page:
            pages = f"{self.starting_page}-{self.ending_page}"
        else:
            pages = "-"

        bib_journal = self.publication_name or ""
        bib_title = self.title or ""
        bib_volume = self.volume or ""
        bib_issue = self.issue_identifier or ""

        bib_parts = [
            f"@article{{{key},",
            f"  author = {{{authors_str}}},",
            f"  title = {{{{{bib_title}}}}},",  # Double braces for BibTeX
            f"  journal = {{{bib_journal}}},",
            f"  year = {{{year}}},",
            f"  volume = {{{bib_volume}}},",
            f"  number = {{{bib_issue}}},",
            f"  pages = {{{pages}}}",
        ]
        if self.doi:
            bib_parts.append(f",\n  doi = {{{self.doi}}}")
        bib_parts.append("}")
        return "\n".join(bib_parts)

    def get_html(self) -> str:
        """Return the bibliographic entry in HTML format."""
        au_link = (
            '<a href="https://www.scopus.com/authid/detail.url'
            '?origin=AuthorProfile&authorId={0}">{1}</a>'
        )
        authors_list = self.authors or []
        if len(authors_list) > 1:
            authors_str_parts = [
                au_link.format(
                    a.auid, f"{a.given_name or ''} {a.surname or ''}".strip()
                )
                for a in authors_list[:-1]
            ]
            authors_str = ", ".join(authors_str_parts)
            last_author = authors_list[-1]
            authors_str += " and " + au_link.format(
                last_author.auid,
                f"{last_author.given_name or ''!s} {last_author.surname or ''!s}".strip(),
            )
        elif authors_list:  # len == 1
            a = authors_list[0]
            authors_str = au_link.format(
                a.auid, f"{a.given_name or ''} {a.surname or ''}".strip()
            )
        else:
            authors_str = "(No author found)"

        title_str = f'<a href="{self.scopus_link or ""}">{self.title or ""}</a>'

        if self.volume and self.issue_identifier:
            volissue = f"<b>{self.volume}({self.issue_identifier})</b>"
        elif self.volume:
            volissue = f"<b>{self.volume}</b>"
        else:
            volissue = "no volume"

        jlink = (
            '<a href="https://www.scopus.com/source/sourceInfo.url'
            f'?sourceId={self.source_id or ""}">{self.publication_name or ""}</a>'
        )
        html_parts = [
            f"{authors_str}, ",
            f"{title_str}, ",
            f"{jlink}, ",
            f"{volissue}, ",
            f"{_parse_pages(self, unicode=True)}, ",
            f"({(self.cover_date or '----')[:4]}).",
        ]
        s = "".join(html_parts)
        if self.doi:
            s += f' <a href="https://doi.org/{self.doi}">doi:{self.doi}</a>.'
        return s

    def get_latex(self) -> str:
        """Return the bibliographic entry in LaTeX format."""
        authors_list = self.authors or []
        if len(authors_list) > 1:
            authors_str = _list_authors(authors_list)
        elif authors_list:  # len == 1
            a = authors_list[0]
            authors_str = f"{a.given_name or ''} {a.surname or ''}".strip()
        else:
            authors_str = "(No author found)"

        if self.volume and self.issue_identifier:
            volissue = f"\\textbf{{{self.volume}({self.issue_identifier})}}"
        elif self.volume:
            volissue = f"\\textbf{{{self.volume}}}"
        else:
            volissue = "no volume"

        title_str = self.title or ""
        pub_name_str = self.publication_name or ""
        cover_date_year = (self.cover_date or "----")[:4]

        s_parts = [
            f"{authors_str}, \\textit{{{title_str}}}, {pub_name_str}, ",
            f"{volissue}, {_parse_pages(self)} ({cover_date_year}).",
        ]
        s = "".join(s_parts)
        if self.doi:
            s += f" \\href{{https://doi.org/{self.doi}}}{{doi:{self.doi}}}, "
        s += f"\\href{{{self.scopus_link or ''}}}{{scopus:{self.eid or ''}}}."
        return s

    def get_ris(self) -> str:
        """
        Return the bibliographic entry in RIS format.

        RIS stands for Research Information System Format.
        For journal articles.

        Raises
        ------
        ValueError
            If the item's aggregation_type is not "Journal".

        """
        if self.aggregation_type != "Journal":
            error_msg = "Only Journal articles supported."
            raise ValueError(error_msg)
        # Basic information
        ris = (
            f"TY  - JOUR\nTI  - {self.title or ''}\nJO  - {self.publication_name or ''}"
            f"\nVL  - {self.volume or ''}\nDA  - {self.cover_date or ''}\n"
            f"PY  - {(self.cover_date or '----')[:4]}\nSP  - {self.page_range or ''}\n"
        )
        # Authors
        authors_list = self.authors or []
        for au in authors_list:
            ris += f"AU  - {au.indexed_name or ''}\n"
        # DOI
        if self.doi:
            ris += f"DO  - {self.doi}\nUR  - https://doi.org/{self.doi}\n"
        # Issue
        if self.issue_identifier:
            ris += f"IS  - {self.issue_identifier}\n"
        ris += "ER  - \n\n"
        return ris


def _get_org(aff: dict) -> str | None:
    """
    Extract organization information from affiliation for authorgroup.

    :param aff: The affiliation dictionary.
    :return: The organization string or None.
    """
    try:
        org = aff["organization"]
        if not isinstance(org, str):
            try:
                org = org["$"]
            except TypeError:  # Multiple names given
                org = ", ".join([d["$"] for d in org if d])
    except KeyError:  # Author group w/o affiliation
        org = None
    return org


def _list_authors(author_list: list) -> str:
    """
    Format a list of authors (Surname, Firstname and Firstname Surname).

    :param author_list: A list of author namedtuples.
    :return: A formatted string of authors.
    """
    if not author_list:
        return ""
    if len(author_list) == 1:
        a = author_list[0]
        return f"{a.given_name or ''} {a.surname or ''}".strip()

    authors_head = ", ".join(
        [f"{a.given_name or ''} {a.surname or ''}".strip() for a in author_list[:-1]]
    )
    last_author = author_list[-1]
    return f"{authors_head} and {last_author.given_name or ''} {last_author.surname or ''}".strip()


def _parse_pages(retrieval_obj: AbstractRetrieval, *, unicode: bool = False) -> str:
    """
    Parse and format page range of a document.

    :param retrieval_obj: The AbstractRetrieval instance.
    :param unicode: Whether to return unicode string.
    :return: The formatted page string.
    """
    if retrieval_obj.page_range:
        pages = f"pp. {retrieval_obj.page_range}"
    elif retrieval_obj.starting_page and retrieval_obj.ending_page:
        pages = f"pp. {retrieval_obj.starting_page}-{retrieval_obj.ending_page}"
    else:
        pages = "(no pages found)"
    if unicode:
        pages = f"{pages}"  # No specific unicode formatting, just returns the string.
    return pages


def _select_by_idtype(item_list: list, id_type: str) -> str | None:
    """
    Return items matching a special idtype.

    :param item_list: A list of items (dictionaries) to search.
    :param id_type: The idtype to match (e.g., "DOI", "SGR").
    :return: The matching item's value or None.
    """
    try:
        return next(d["$"] for d in item_list if d["@idtype"] == id_type)
    except (IndexError, StopIteration):  # StopIteration if generator is empty
        return None
