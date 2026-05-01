"""Unit tests for ``finqual.node_classes.node_tree.NodeTree``."""

import pytest

from finqual.node_classes.node import Node
from finqual.node_classes.node_tree import NodeTree


def make_tree():
    """
    Build a small accounting-style tree:

        Total Assets (debit)
        ├── Current Assets (debit)
        │   ├── Cash (debit)
        │   └── Receivables (debit)
        └── Non-current Assets (debit)
            └── PPE (debit)
    """
    root = Node("Total Assets"); root.add_balance("debit")

    ca = Node("Current Assets"); ca.add_balance("debit")
    cash = Node("Cash"); cash.add_balance("debit")
    rec = Node("Receivables"); rec.add_balance("debit")
    ca.add_child(cash); ca.add_child(rec)

    nca = Node("Non-current Assets"); nca.add_balance("debit")
    ppe = Node("PPE"); ppe.add_balance("debit")
    nca.add_child(ppe)

    root.add_child(ca); root.add_child(nca)
    return root, [cash, rec, ppe, ca, nca]


def test_traverse_returns_all_descendants():
    root, _ = make_tree()
    tree = NodeTree([root])
    nodes = tree.traverse(root)
    codes = sorted(n.code for n in nodes)
    assert codes == sorted([
        "Total Assets", "Current Assets", "Cash", "Receivables",
        "Non-current Assets", "PPE",
    ])


def test_find_node_by_code_hit_and_miss(capsys):
    root, _ = make_tree()
    tree = NodeTree([root])

    found = tree.find_node_by_code("PPE")
    assert found is not None and found.code == "PPE"

    missing = tree.find_node_by_code("DoesNotExist")
    assert missing is None
    captured = capsys.readouterr()
    assert "Node DoesNotExist not found." in captured.out


def test_get_value_raises_without_sec_data():
    root, _ = make_tree()
    tree = NodeTree([root])
    with pytest.raises(ValueError):
        tree.get_value(root)


def test_get_value_direct_lookup_takes_precedence():
    root, _ = make_tree()
    tree = NodeTree([root])
    # Direct value present — children are ignored.
    tree.load_sec_data({"Total Assets": 99.0, "Cash": 1.0, "Receivables": 2.0, "PPE": 3.0})
    assert tree.get_value(root) == 99.0


def test_get_value_aggregates_children_when_no_direct_value():
    root, _ = make_tree()
    tree = NodeTree([root])
    tree.load_sec_data({"Cash": 10.0, "Receivables": 20.0, "PPE": 70.0})
    # Same-balance children → all added.
    assert tree.get_value(root) == 100.0


def test_get_value_subtracts_opposite_balance_children():
    """If a child has the opposite balance, its value is subtracted."""
    parent = Node("Net"); parent.add_balance("debit")
    income = Node("Income"); income.add_balance("debit")
    expense = Node("Expense"); expense.add_balance("credit")
    parent.add_child(income); parent.add_child(expense)

    tree = NodeTree([parent])
    tree.load_sec_data({"Income": 100.0, "Expense": 30.0})
    assert tree.get_value(parent) == 70.0


def test_get_all_values_populates_node_attributes():
    root, _ = make_tree()
    tree = NodeTree([root])
    tree.load_sec_data({"Cash": 1.0, "Receivables": 2.0, "PPE": 4.0})
    tree.get_all_values()

    # Every node now has a populated value.
    for n in tree.traverse(root):
        assert n.value is not None
    assert root.value == 7.0


def test_to_df_returns_none_when_empty():
    leaf = Node("Empty"); leaf.add_balance("debit")
    tree = NodeTree([leaf])
    # No SEC data loaded — would raise on get_all_values, so use direct .value=None
    assert tree.to_df() is None


def test_to_df_returns_only_populated_nodes():
    root, _ = make_tree()
    tree = NodeTree([root])
    tree.load_sec_data({"Cash": 1.0, "Receivables": 2.0, "PPE": 4.0})
    tree.get_all_values()

    df = tree.to_df()
    assert df is not None
    assert df.height == 6  # 3 leaves + 2 mid + 1 root
    assert "code" in df.columns
    assert "value" in df.columns
