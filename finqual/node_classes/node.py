# node.py

class Node:

    def __init__(self, code):
        self.code = code
        self.children = []
        self.balance = None
        self.description = None
        self.period_type = None
        self.value = None
        self.disclosure = None

    def add_child(self, child_node):
        self.children.append(child_node)

    def add_balance(self, balance_type):
        self.balance = balance_type

    def add_description(self, description_type):
        self.description = description_type

    def add_period_type(self, period_type):
        self.period_type = period_type

    def add_value(self, value):
        self.value = value

    def add_disclosure(self, disclosure):
        self.disclosure = disclosure

    def to_dict(self):
        return {
            "name": self.code,
            "children": [child.to_dict() for child in self.children],
            "balance": self.balance,
            "description": self.description,
            "period_type": self.period_type,
            "disclosure": self.disclosure,
        }

    def copy(self):
        """Return a deep copy of this node and all its descendants."""
        new_node = Node(self.code)
        new_node.balance = self.balance
        new_node.description = self.description
        new_node.period_type = self.period_type
        new_node.value = self.value
        new_node.disclosure = self.disclosure
        new_node.children = [child.copy() for child in self.children]
        return new_node

    @staticmethod
    def from_dict(data):
        node = Node(data["name"])
        node.children = [Node.from_dict(child) for child in data.get("children", [])]
        node.balance = data.get("balance")
        node.description = data.get("description")
        node.period_type = data.get("period_type")
        node.disclosure = data.get("disclosure")
        return node

    def __repr__(self):
        return f"Node({self.code!r})"
