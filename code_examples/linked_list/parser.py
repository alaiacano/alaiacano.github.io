import asyncio
import copy
import logging
import yaml

from tasks import task_factory, Task
from ll import LinkedList

from collections import defaultdict

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logging.basicConfig(level="INFO")


@dataclass
class TaskDefinition:
    """
    Converts a task from the yaml config into a dataclass.

    Required fields are `name` and `action`. All other key -> value pairs listed in the yaml file will
    be passed to a `params` dict.
    """

    name: str
    action: str
    params: dict = field(default_factory=dict)

    id: Optional[int] = None
    parent: Optional[int] = None

    @staticmethod
    def from_dict(d: dict):
        if "name" not in d.keys():
            raise ValueError("task is missing a required 'name' field")
        if "action" not in d.keys():
            raise ValueError("task is missing a required 'action' field")
        if "config" in d.keys():
            params = {k: v for (k, v) in d["config"].items()}
        else:
            params = {}

        # fields for the async execution
        id = d["id"] if "id" in d.keys() else None
        parent = d["parent"] if "parent" in d.keys() else None

        return TaskDefinition(
            name=d["name"], action=d["action"], params=params, id=id, parent=parent
        )


class Parser:
    """
    Parses the pipeline yaml into a list of TaksDefinitions, and provides methods to describe and ultimately execute the pipeline.
    """

    def __init__(self, path):
        self.pipeline: dict = yaml.safe_load(open(path))
        self.task_definitions: List[TaskDefinition] = []

    def parse(self):
        api_version = self.pipeline["apiVersion"]
        if api_version != 1:
            raise ValueError("I only know API v1")

        if "tasks" not in self.pipeline.keys():
            raise ValueError("malformed yaml - you need an array of tasks")

        # parse the task definitions
        self.task_definitions = [
            TaskDefinition.from_dict(t) for t in self.pipeline["tasks"]
        ]

    def describe(self):
        if len(self.task_definitions) == 0:
            print("No tasks parsed yet")
            return

        print("~~ Tasks that will execute ~~")
        for t in self.task_definitions:
            print(f"{t.action} - {t.name} - {t.params}")

    def run(self):
        prev_task: Optional[Task] = None

        for task_def in self.task_definitions:
            prev_ll: LinkedList = prev_task.linked_list if prev_task is not None else LinkedList()
            task: Task = task_factory(task_def.action, task_def.name, prev_ll)
            logging.info("~~~")
            task.execute(**task_def.params)
            prev_task = task


class Parser2:
    def __init__(self, path):
        self.pipeline: dict = yaml.safe_load(open(path))
        self.task_definitions: Dict[int, TaskDefinition] = {}
        self.graph: Dict[int, List[TaskDefinition]] = defaultdict(list)

    def parse(self):
        api_version = self.pipeline["apiVersion"]
        if api_version != 2:
            raise ValueError("I only know API v2")

        if "tasks" not in self.pipeline.keys():
            raise ValueError("malformed yaml - you need an array of tasks")

        # parse the task definitions
        for t in self.pipeline["tasks"]:
            td = TaskDefinition.from_dict(t)
            self.task_definitions.update({td.id: td})
            self.graph[td.parent].append(td)

    def run_task(self, task_id: Optional[int], input_ll: LinkedList, visited: Set[int]):
        logging.info("--------")
        visited.add(task_id)

        # run the task
        task_definition = self.task_definitions[task_id]
        logging.info(f"Visiting task {task_definition.id}")
        parent_task = task_factory(
            task_definition.action, task_definition.name, input_ll
        )
        parent_task.execute(**task_definition.params)

        # If the task has children that have not yet been executed, run those recursively.
        for child_task in self.graph[task_id]:
            if child_task.id not in visited:
                # kinda gross here, but python only does pass-by-reference and we need to be able to mutate
                # the LinkedList within each task.
                ll = copy.deepcopy(parent_task.linked_list)
                self.run_task(child_task.id, ll, visited)

    def run(self):
        first_task_id = self.graph[None][0].id
        self.run_task(first_task_id, LinkedList(), set([]))


if __name__ == "__main__":
    # p = Parser("pipeline.yaml")
    # p.parse()
    # p.describe()
    # p.run()

    p = Parser2("pipeline2.yaml")
    p.parse()
    p.run()
