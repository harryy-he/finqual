
import polars as pl

class NodeTree:
    """
    Container and utility class for working with hierarchical `Node` structures.

    This class provides tools for loading SEC data into a node hierarchy, traversing
    the tree, computing aggregated values based on financial statement rules, and
    exporting results to a Polars DataFrame.

    Attributes
    ----------
    node_tree : list[Node]
        A list of root nodes defining the full hierarchical tree structure.
    sec_data : dict[str, Any] | None
        Mapping of node codes to numerical values sourced from SEC data.
        Assigned via `load_sec_data`.
    """
    def __init__(self, node_tree) -> None:
        """
        Initialize the NodeTree with a list of root nodes.

        Parameters
        ----------
        node_tree : Iterable[Node]
            The root-level nodes representing the hierarchical tree.
        """
        self.node_tree = node_tree
        self.sec_data = None

    def load_sec_data(self, sec_data: dict) -> None:
        """
        Load SEC label/value data into the tree for later aggregation.

        Parameters
        ----------
        sec_data : dict[str, Any]
            Dictionary mapping node codes → numerical values.
        """
        self.sec_data = sec_data

    def traverse(self, node) -> list:
        """
        Recursively traverse a node and return a flat list of it and its descendants.

        Parameters
        ----------
        node : Node
            The starting node for traversal.

        Returns
        -------
        list[Node]
            All nodes in the subtree including the starting node.
        """
        node_list = [node]
        for child in node.children:
            node_list.extend(self.traverse(child))
        return node_list

    def find_node_by_code(self, code: str):
        """
        Search the entire tree for a node with the given code.

        Parameters
        ----------
        code : str
            The node code to search for.

        Returns
        -------
        Node or None
            The matching node if found, otherwise None.
        """
        def _find(node):
            if node.code == code:
                return node
            for child in node.children:
                result_ = _find(child)
                if result_:
                    return result_
            return None

        for root in self.node_tree:
            result = _find(root)
            if result:
                return result
        print(f"Node {code} not found.")
        return None

    def get_value(self, node) -> None | float:
        """
        Compute the value of a node based on SEC data and child aggregation rules.

        The node value is determined using these rules:
        - If the node has a direct SEC value, return it.
        - Otherwise, sum the values of its children.
        - Child values are added or subtracted depending on balance type:
          if child.balance == node.balance → add
          else → subtract.

        Parameters
        ----------
        node : Node
            The node whose value should be computed.

        Returns
        -------
        float or None
            The calculated value, or None if no data is available.
        """
        if self.sec_data is None:
            raise ValueError("No SEC data is loaded, please call the 'load_sec_data' method.")

        else:
            value = self.sec_data.get(node.code, None)
            if value is not None:
                return value

            child_values = [v if child.balance == node.balance else -v for child in node.children if (v := self.get_value(child)) is not None]

            if child_values:
                return sum(child_values)

            return None

    def get_all_values(self) -> list:
        """
        Compute and store values for all nodes in the tree.

        Each node with a computable value will have its `.value` attribute set.

        Returns
        -------
        list[Node]
            The root nodes (same structure as `node_tree`), now enriched with values.
        """
        if self.sec_data is None:
            raise ValueError("No SEC data is loaded, please call the 'load_sec_data' method.")

        else:
            def collect(node):
                value = self.get_value(node)
                if value is not None:
                    node.add_value(value)
                for child in node.children:
                    collect(child)

            for root in self.node_tree:
                collect(root)

            return self.node_tree

    def to_df(self) -> pl.DataFrame:
        """
        Convert all nodes with computed values into a Polars DataFrame.

        Only nodes where `node.value` is not None are included.

        Returns
        -------
        pl.DataFrame or None
            A Polars DataFrame containing node metadata and computed values,
            or None if the tree has no populated value rows.
        """
        def flatten(node):
            if node.value is not None:
                rows.append({
                    "code": node.code,
                    "balance": node.balance,
                    "period_type": node.period_type,
                    "description": node.description,
                    "value": node.value,
                    "disclosure": node.disclosure,
                })

                for child in node.children:
                    flatten(child)

        # ---

        rows = []

        for root in self.node_tree:
            flatten(root)

        if len(rows) > 0:
            df = pl.DataFrame(rows)

            return df
