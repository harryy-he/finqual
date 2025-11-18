# node.py

class Node:
    """
    Represents a node within a hierarchical data structure.

    This class is designed for building tree-like representations of financial,
    taxonomic, or organizational data. Each node may contain metadata such as
    balance type, description, reporting period type, disclosure information,
    and an optional value. Nodes can have unlimited children, enabling the
    construction of nested hierarchies.

    Attributes
    ----------
    code : str
        Unique identifier or label for this node.
    children : list[Node]
        Child nodes that belong to this node in the hierarchy.
    balance : str | None
        Balance classification (e.g., "credit", "debit"), if applicable.
    description : str | None
        Textual description associated with the node.
    period_type : str | None
        Reporting period classification (e.g., "instant", "duration").
    value : Any | None
        Optional numeric or textual value stored in the node.
    disclosure : str | None
        Additional disclosure information or metadata related to the node.
    """
    def __init__(self, code):
        """
        Initialize a new Node.

        Parameters
        ----------
        code : str
            Unique identifier for the node.
        """
        self.code = code
        self.children = []
        self.balance = None
        self.description = None
        self.period_type = None
        self.value = None
        self.disclosure = None

    def add_child(self, child_node) -> None:
        """
        Attach a child node to this node.

        Parameters
        ----------
        child_node : Node
            The node to be added as a descendant.
        """
        self.children.append(child_node)

    def add_balance(self, balance_type: str) -> None:
        """
        Set the balance type for the node.

        Parameters
        ----------
        balance_type : str
            Balance category (e.g., "credit", "debit").
        """
        self.balance = balance_type

    def add_description(self, description_type: str) -> None:
        """
        Assign a description to the node.

        Parameters
        ----------
        description_type : str
            Text description of the node.
        """
        self.description = description_type

    def add_period_type(self, period_type: str) -> None:
        """
        Set the period type for the node.

        Parameters
        ----------
        period_type : str
            Period classification (e.g., "instant", "duration").
        """
        self.period_type = period_type

    def add_value(self, value: int | float) -> None:
        """
        Store a value in the node.

        Parameters
        ----------
        value : int | flota
            Numeric or textual value associated with this node.
        """
        self.value = value

    def add_disclosure(self, disclosure: str) -> None:
        """
        Add disclosure information to the node.

        Parameters
        ----------
        disclosure : str
            Supplemental disclosure or metadata.
        """
        self.disclosure = disclosure

    def to_dict(self) -> dict[str]:
        """
        Convert the node and all its descendants into a dictionary.

        Returns
        -------
        dict
            A nested dictionary representation of the node hierarchy.
        """
        return {
            "name": self.code,
            "children": [child.to_dict() for child in self.children],
            "balance": self.balance,
            "description": self.description,
            "period_type": self.period_type,
            "disclosure": self.disclosure,
        }

    def copy(self):
        """
        Create a deep copy of this node and all of its children.

        Returns
        -------
        Node
            A fully independent copy of the node hierarchy.
        """
        new_node = Node(self.code)
        new_node.balance = self.balance
        new_node.description = self.description
        new_node.period_type = self.period_type
        new_node.value = self.value
        new_node.disclosure = self.disclosure
        new_node.children = [child.copy() for child in self.children]
        return new_node

    @staticmethod
    def from_dict(data: dict):
        """
        Reconstruct a Node instance from a dictionary (reverse of `to_dict`).

        Parameters
        ----------
        data : dict
            Dictionary containing serialized node information.

        Returns
        -------
        Node
            Root node reconstructed from the dictionary.
        """
        node = Node(data["name"])
        node.children = [Node.from_dict(child) for child in data.get("children", [])]
        node.balance = data.get("balance")
        node.description = data.get("description")
        node.period_type = data.get("period_type")
        node.disclosure = data.get("disclosure")
        return node

    def __repr__(self):
        return f"Node({self.code!r})"
