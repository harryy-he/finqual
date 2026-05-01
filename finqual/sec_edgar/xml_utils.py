"""
Shared helpers for SEC XML form parsing.

Centralises:
- ``gettext``               — namespace-aware safe text extraction.
- ``safe_get_xml``          — HTTP fetch with timeout, status handling and parse-error wrapping.

Previously ``gettext`` was duplicated verbatim across :mod:`form_4` and
:mod:`form_13`, and neither file set a ``timeout`` on its ``requests.get`` call.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Mapping, Optional

import requests

# Default network timeout for SEC XML fetches.
DEFAULT_TIMEOUT_SECS = 30


def gettext(parent: Optional[ET.Element], path: str, namespaces: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """
    Return ``parent.find(path, namespaces).text`` or ``None`` if missing.

    A small but very common helper — saves ``if el is not None`` boilerplate
    everywhere in the form-parsing code.

    Parameters
    ----------
    parent : xml.etree.ElementTree.Element or None
        Element to search under. ``None`` is permitted (returns ``None``).
    path : str
        XPath expression understood by ``ElementTree``.
    namespaces : Mapping[str, str], optional
        Namespace map forwarded to ``Element.find``.
    """
    if parent is None:
        return None
    el = parent.find(path, namespaces) if namespaces else parent.find(path)
    return el.text if el is not None else None


def safe_get_xml(url: str, headers: Mapping[str, str], timeout: int = DEFAULT_TIMEOUT_SECS) -> ET.Element:
    """
    Fetch ``url`` and return its parsed XML root element.

    Parameters
    ----------
    url : str
        Target URL.
    headers : Mapping[str, str]
        HTTP headers (typically the project's :data:`sec_headers`).
    timeout : int, default ``DEFAULT_TIMEOUT_SECS``
        Network timeout in seconds.

    Returns
    -------
    xml.etree.ElementTree.Element
        Root element of the parsed XML document.

    Raises
    ------
    requests.HTTPError
        If the HTTP response indicates failure.
    xml.etree.ElementTree.ParseError
        If the response body is not valid XML.
    """
    resp = requests.get(url, headers=dict(headers), timeout=timeout)
    resp.raise_for_status()
    return ET.fromstring(resp.content)


__all__ = ["gettext", "safe_get_xml", "DEFAULT_TIMEOUT_SECS"]
