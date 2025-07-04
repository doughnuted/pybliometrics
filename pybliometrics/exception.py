"""Base exceptions and classes for pybliometrics.scopus."""


# Base classes
class ScopusException(Exception):
    """Base class for exceptions in pybliometrics."""


class ScopusError(ScopusException):
    """Exception for a serious error in pybliometrics."""


# Query errors
class ScopusQueryError(ScopusException):
    """Exception for problems related to Scopus queries."""


# HTML errors
class ScopusHtmlError(ScopusException):
    """Wrapper for exceptions raised by requests."""


class Scopus400Error(ScopusHtmlError):
    """Raised if a query yields a 400 error (Bad Request for url)."""


class Scopus401Error(ScopusHtmlError):
    """Raised if a query yields a 401 error (Unauthorized for url)."""


class Scopus403Error(ScopusHtmlError):
    """Raised if a query yields a 403 error (Forbidden for url)."""


class Scopus404Error(ScopusHtmlError):
    """Raised if a query yields a 404 error (Not Found for url)."""


class Scopus407Error(ScopusHtmlError):
    """Raised if a query yields a 407 error (Proxy Authentication Required)."""


class Scopus413Error(ScopusHtmlError):
    """
    Raised if a query yields a 413 error (Request Entity Too
    Large for url).
    """


class Scopus414Error(ScopusHtmlError):
    """Raised if a query yields a 414 error (Request-URI Too Large for url)."""


class Scopus429Error(ScopusHtmlError):
    """Raised if a query yields a 429 error (Quota exceeded)."""


class ScopusServerError(ScopusHtmlError):
    """Wrapper for Server related exceptions (code 5xx)."""
