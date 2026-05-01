"""Unit tests for ``finqual.node_classes.node.Node``."""

from finqual.node_classes.node import Node


def test_init_defaults():
    n = Node("A")
    assert n.code == "A"
    assert n.children == []
    assert n.balance is None
    assert n.description is None
    assert n.period_type is None
    assert n.value is None
    assert n.disclosure is None


def test_add_child_appends():
    parent = Node("P")
    child = Node("C")
    parent.add_child(child)
    assert parent.children == [child]


def test_add_metadata_setters():
    n = Node("X")
    n.add_balance("credit")
    n.add_description("desc")
    n.add_period_type("instant")
    n.add_value(123.45)
    n.add_disclosure("note")
    assert n.balance == "credit"
    assert n.description == "desc"
    assert n.period_type == "instant"
    assert n.value == 123.45
    assert n.disclosure == "note"


def test_to_dict_serialises_subtree():
    root = Node("R")
    root.add_balance("debit")
    root.add_description("root node")
    child = Node("C1")
    child.add_balance("credit")
    root.add_child(child)

    d = root.to_dict()
    assert d == {
        "name": "R",
        "balance": "debit",
        "description": "root node",
        "period_type": None,
        "disclosure": None,
        "children": [
            {
                "name": "C1",
                "balance": "credit",
                "description": None,
                "period_type": None,
                "disclosure": None,
                "children": [],
            }
        ],
    }


def test_from_dict_round_trip():
    payload = {
        "name": "R",
        "balance": "debit",
        "description": "root",
        "period_type": "duration",
        "disclosure": None,
        "children": [
            {"name": "C", "balance": "credit", "description": None,
             "period_type": None, "disclosure": None, "children": []}
        ],
    }
    n = Node.from_dict(payload)
    assert n.code == "R"
    assert n.balance == "debit"
    assert n.period_type == "duration"
    assert len(n.children) == 1
    assert n.children[0].code == "C"


def test_copy_produces_deep_copy():
    root = Node("R")
    child = Node("C")
    child.add_value(10)
    root.add_child(child)

    clone = root.copy()
    # Mutate clone — original must not change.
    clone.children[0].add_value(999)
    assert root.children[0].value == 10
    assert clone.children[0].value == 999
    # Different identities all the way down.
    assert clone is not root
    assert clone.children[0] is not root.children[0]


def test_repr_uses_code():
    assert repr(Node("ABC")) == "Node('ABC')"
