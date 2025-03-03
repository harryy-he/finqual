# Node class and respective functions
"""
Tree class
"""

class Node():
    def __init__(self, name, children=None, parent=None, attribute=None):
        self.name = name
        self.children = []
        self.parent = parent
        self.attribute = attribute

        if children is not None:
            for child in children:
                child.parent = self

        if parent is not None:
            parent.addNode(self)

    def addNode(self, obj):
        """
        Add the child "obj" to the node "self"
        """
        self.children.append(obj)
        obj.parent = self

    def getRootParent(self):
        """
        Returns the root parent node of a given node
        """
        while (self.parent != None):
            self = self.parent

        return self

    def getChildrenNames(self):
        return [child.name for child in self.children]

    def getChildrenNodes(self):
        return self.children

    def dfs(self, visited):
        """
        A depth-first search function that takes in a Node class and an empty list "visited", returning a list of all the children of that Node
        """
        visited.append(self.name)

        for child in self.children:
            child.dfs(visited)

        return visited