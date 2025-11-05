
import polars as pl

class NodeTree:

    def __init__(self, node_tree):
        """
        :param node_tree: Takes in a json file
        """
        self.node_tree = node_tree
        self.sec_data = None

    def load_sec_data(self, sec_data: dict):
        """
        Takes in a dictionary containing key, value pairs of SEC label and the respective value
        """
        self.sec_data = sec_data

    def traverse(self, node):
        node_list = [node]
        for child in node.children:
            node_list.extend(self.traverse(child))
        return node_list

    def find_node_by_code(self, code):
        """
        Finds and returns the node with the given code from the tree.
        Searches from all root nodes.

        :param code: The code of the node to find.
        :return: Node object if found, else None.
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

    def get_value(self, node):

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

    def get_all_values(self) -> dict:

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

    def to_df(self):

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
