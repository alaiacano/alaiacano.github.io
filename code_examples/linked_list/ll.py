# Modified from the solution provided at https://www.geeksforgeeks.org/reverse-a-linked-list/
from dataclasses import dataclass
from typing import Any, Optional, Type


@dataclass
class Node:
    value: int
    data: Optional[Type["Node"]] = None


class LinkedList:
    def __init__(self):
        self.head: Optional[Node] = None
        self.next: Optional[Node] = None

    def reverse(self):
        """
        The business! Reverses the linked list.
        """
        prev: Optional[Node] = None
        current: Node = self.head
        while current is not None:
            next = current.next
            current.next = prev
            prev = current
            current = next
        self.head = prev

    def push(self, v):
        """
        Adds a new node to the head of the linked list.

        1. Makes a new Node
        2. Sets the current head to the tail of the new node
        3. Sets self.head to the new node.
        """
        new_node = Node(v)
        new_node.next = self.head
        self.head = new_node

    def __repr__(self):
        """
        String representation of the list, from head to tail.
        """
        values = []
        node = self.head
        while node is not None:
            values.append(str(node.value))
            node = node.next
        return ", ".join(values)
