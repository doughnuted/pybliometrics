"""Module for retrieving article entitlement information from ScienceDirect."""

from __future__ import annotations

from pybliometrics.superclasses import Retrieval
from pybliometrics.utils import (
    VIEWS,
    chained_get,
    check_parameter_value,
    detect_id_type,
)


class ArticleEntitlement(Retrieval):
    """Class to retrieve the entitlement status for a document from ScienceDirect."""

    @property
    def status(self) -> str | None:
        """Status of whether a document has been found."""
        return self._json.get("@status")

    @property
    def identifier(self) -> str | None:
        """Identifier of a document."""
        return self._json.get("dc:identifier")

    @property
    def eid(self) -> str | None:
        """The EID of a document."""
        return self._json.get("eid")

    @property
    def entitled(self) -> str | None:
        """Entitlement status of a document."""
        return self._json.get("entitled")

    @property
    def link(self) -> str | None:
        """ScienceDirect canonical URL."""
        return chained_get(self._json, ["link", "@href"])

    @property
    def message(self) -> str | None:
        """Entitlement status message."""
        return self._json.get("message")

    @property
    def pii(self) -> str | None:
        """The PII of a document."""
        return self._json.get("pii")

    @property
    def pii_norm(self) -> str | None:
        """The PII-norm of a document."""
        return self._json.get("pii-norm")

    @property
    def doi(self) -> str | None:
        """The DOI of a document."""
        return self._json.get("prism:doi")

    @property
    def pubmed_id(self) -> str | None:
        """The Pubmed ID of a document (when used in the request)."""
        return self._json.get("pubmed_id")

    @property
    def url(self) -> str | None:
        """API URL used to check entitlement."""
        return self._json.get("prism:url")

    @property
    def scopus_id(self) -> str | None:
        """The Scopus ID of a document (when used in the request)."""
        return self._json.get("scopus_id")

    def __init__(
        self,
        identifier: int | str,
        *,
        view: str = "FULL",
        id_type: str | None = None,
        refresh: bool | int = False,
        **kwds: str,
    ) -> None:
        """
        Interaction with the Article Entitlement API.

        :param identifier: The identifier of a document.
        :param view: The view of the file that should be downloaded.  Allowed
                     values: `FULL`, `STANDARD`.  Default: `FULL`.
        :param id_type: The type of used ID.  Allowed values: `eid`, `pii`,
                        `scopus_id`, `pubmed_id`, `doi`, `pui`.
        :param refresh: Whether to refresh the cached file if it exists or not.
                        If int is passed, cached file will be refreshed if the
                        number of days since last modification exceeds that value.
        :param kwds: Keywords passed on as query parameters.  Must contain
                     fields and values mentioned in the
                     `API specification <https://dev.elsevier.com/documentation/ArticleEntitlementAPI.wadl>`_.
        """
        # Checks
        identifier = str(identifier)
        check_parameter_value(view, VIEWS["ArticleEntitlement"], "view")
        if not id_type:
            id_type = detect_id_type(identifier)
        else:
            allowed_id_types = ("eid", "pii", "scopus_id", "pubmed_id", "doi", "pui")
            check_parameter_value(id_type, allowed_id_types, "id_type")

        self._view = view
        self._refresh = refresh
        # Retrieve and get content
        Retrieval.__init__(self, identifier=identifier, id_type=id_type, **kwds)
        self._json = chained_get(
            self._json, ["entitlement-response", "document-entitlement"]
        )

    def __str__(self) -> str:
        """Return a string representation of the object."""
        s = self.message
        s += f" with doi: {self.doi}"
        return s
