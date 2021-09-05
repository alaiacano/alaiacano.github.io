import logging
from abc import ABC, abstractmethod
from copy import copy
from ll import LinkedList, Node
from typing import List, Optional

logging.basicConfig(level="INFO")


def task_factory(action: str, name: str, lst: LinkedList):
    """
    For the given `action`, produces the appropriate subclass of `Task`.
    """
    if action == "push_values":
        return PushValuesTask(name, lst)
    if action == "print_list":
        return PrintListTask(name, lst)
    if action == "reverse_list":
        return ReverseListTask(name, lst)

    raise ValueError(f"Unknown action: {name}")


class Task(ABC):
    def __init__(self, name: str, lst: LinkedList):
        """
        name: The name of this task, describing what it will do.
        lst: The LinkedList that we will perform actions on. This could be an empty list or contain many nodes.
        """
        self._name = name
        self._lst: LinkedList = lst

    @property
    def name(self) -> str:
        """The name of the task"""
        return self._name

    @property
    def linked_list(self) -> LinkedList:
        """Returns the list that we are working on"""
        return self._lst

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        This method must be implemented by any Task subclass to carry out it's job-specific logic.
        """
        pass


class PushValuesTask(Task):
    def execute(self, *args, **kwargs):
        logging.info(f"Populating the list with: {kwargs['elements']}")
        for v in kwargs["elements"]:
            self._lst.push(v)


class PrintListTask(Task):
    def execute(self, *args, **kwargs):
        print(f"the list is: {self._lst}")


class ReverseListTask(Task):
    def execute(self, *args, **kwargs):
        logging.info("Reversing the list")
        self._lst = ReverseListTask.reverse(self._lst)

    @staticmethod
    def reverse(lst: LinkedList):
        """
        The business! Reverses the linked list.
        """
        prev: Optional[Node] = None
        current: Node = lst.head
        while current is not None:
            next = current.next
            current.next = prev
            prev = current
            current = next
        lst.head = prev
        return lst
