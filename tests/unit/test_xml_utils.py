"""Unit tests for ``finqual.sec_edgar.xml_utils``."""

import xml.etree.ElementTree as ET

from finqual.sec_edgar.xml_utils import gettext


def test_gettext_returns_text_when_present():
    root = ET.fromstring("<root><a>hello</a></root>")
    assert gettext(root, "a") == "hello"


def test_gettext_returns_none_when_missing():
    root = ET.fromstring("<root><a>hello</a></root>")
    assert gettext(root, "missing") is None


def test_gettext_returns_none_when_parent_is_none():
    assert gettext(None, "a") is None


def test_gettext_with_namespace():
    xml = """<root xmlns:ns="http://example.com/ns">
                <ns:item>value</ns:item>
             </root>"""
    root = ET.fromstring(xml)
    assert gettext(root, "ns:item", {"ns": "http://example.com/ns"}) == "value"
