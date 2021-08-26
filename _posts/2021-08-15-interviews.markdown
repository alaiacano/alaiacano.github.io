---
layout: post
title: "Code Interviews"
date: 2021-08-10 20:18:32 -0500
categories: interviews
---

For most of us, interviewing is hard. And annoying, frustrating, and stressful. Most interviews these days consist of a string of 1-hour interviews covering:

- Programming (sometimes 2 of these).
- Systems design.
- 1-2 specialization-specific interviews: ML, Data Engineering, Frontend, Distributed Systems, etc.
- An interview with a hiring manager. Sometimes this is about "leadership" or other general topics depending on the role.

The programming interview is probably the most hated. I personally don't like being on either side of these interviews. Leetcode-style problems that test _CS fundamentals_ can be fun puzzles for some people, and are arguably a decent evaluation of junior engineers without industry experience, but it's a common complaint among senior engineers that they have to study material that they haven't used in years to get a job where they won't use it. This tweet, from the author of [Homebrew](https://brew.sh/), lives in infamy.

<blockquote class="twitter-tweet" data-dnt="true" data-theme="dark"><p lang="en" dir="ltr">Google: 90% of our engineers use the software you wrote (Homebrew), but you can’t invert a binary tree on a whiteboard so fuck off.</p>&mdash; Max Howell (@mxcl) <a href="https://twitter.com/mxcl/status/608682016205344768?ref_src=twsrc%5Etfw">June 10, 2015</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

There are a few questions that people like to use as punching bags. Invert a binary tree. Reverse a linked list. Perform breadth-first and/or depth-first tree traversals. Anything to do with heaps. I recently read the [history of the "Reverse A Linked List" problem](https://www.hillelwayne.com/post/linked-lists/) and find this take fascintating. The goal wasn't to reverse a linked list, it was to make sure you are familiar with pointer manipulation in c, and reversing the linked list was a good way to demonstrate that.

> In the early 80’s, C programmers were in high demand. Interviewers used questions that specifically tested your experience with C, which meant problems involving lots of pointer manipulation. This ingrained LL questions as a cultural institution in many places, especially places doing lots of low-level work, like Microsoft and Google. From there, it was exported to the wider software world, and lacking the original context, people assumed it was about “testing CS fundamentals” or “quick thinking”.

The fact remains that it's an important part of an interview to make sure that a software engineer can code. So if we're going to be asked to reverse a linked list, what is the real underlying assessment? In 2021, that is probably no longer about pointer manipulation. What should it be about, then? Let's dig in and have some fun.

## Reversing a Linked List

We'll start with the classic algorithm question. My solution is [here](https://gist.github.com/alaiacano/35a63e7631b60641fc0342f31461b80d#file-ll-py). Inserting new nodes at the head of the list is `O(1)` and reversing the list is `O(N)`, and does so by moving pointers around and not making a full copy of the list in memory.

To populate, print, reverse, and then print the list again, we'd do this:

```python
from ll import LinkedList

if __name__ == "__main__":
    ll = LinkedList()
    ll.push(1)
    ll.push(2)
    ll.push(3)
    ll.push(4)

    print(f"The list is: {ll}")
    # The list is: 4, 3, 2, 1
    ll.reverse()
    print(f"The reversed list is {ll}")
    # Tthe list is: 1, 2, 3, 4
```

Wonderful. In the real world, we would have used [`List.reverse`](https://github.com/python/cpython/blob/e5c8ddb1714fb51ab1defa24352c98e0f01205dc/Objects/listobject.c#L1042-L1056) from the standard library, but this produces the same result. Would we have run the code in a module like this? Probably not!

## Enter the LinkedList Pipeline

Let's rewrite how we use this `LinkedList` class into something a little more _modern_:

```yaml
apiVersion: 1
tasks:
  - name: "populate the list"
    action: push_values
    config:
      elements:
        - 1
        - 2
        - 3
        - 4
  - name: "print the list"
    action: print_list
  - name: "reverse the list"
    action: reverse_list
  - name: "print the reversed list"
    action: print_list
```

YAML! Nice. Yaml is fun to joke about, but Vicki Boykis posted [a twitter poll](https://twitter.com/vboykis/status/1407821631997759488) about which languages people use in Data Science/ML and the most common reply was "does yaml count?" If everyone asks, it means yes.

The above yaml does not actually do anything, and this is ostensibly a post about software coding interviews, so let's build something that reverses a linked list given this pipeline definition. Is this overkill for the goal of reversing a 4-element linked list? Sure. But it's a good analog to the modular systems that we are paid to build and use as software engineers (especially Data/ML engineers). It's the kind of thing that we actually do every day, and should be familiar with. In other words, **Components are the new Pointers.**

So let's dive in.

### Coding problem: Implement a framework to execute this pipeline

First we'll need to define a `Task` class to carry out the logic of each `task` defined in the yaml. A `Task` may take an input `LinkedList` from a previous `Task`, performs some operation on it, and produces an output. Here's the interface:

```python
from abc import ABC, abstractmethod
from ll import LinkedList

class Task(ABC):
    def __init__(self, name: str, lst: LinkedList):
        self._name = name
        self._lst: LinkedList = lst

    @property
    def name(self) -> str:
        return self._name

    @property
    def linked_list(self) -> LinkedList:
        return self._lst

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
```

It takes an input `LinkedList` and a `name` for the task, and has an abstract `execute` method that will have to mutate `self._lst` (which is maybe not ideal but we'll work with it). Let's extend `Task` to perform the actions seen in the yaml: `push_values`, `reverse_list`, and `print_list`.

```python
import logging

class PushValuesTask(Task):
    def execute(self, *args, **kwargs):
        logging.info(f"Populating the list with: {kwargs['elements']}")
        for v in kwargs["elements"]:
            self._lst.push(v)

class ReverseListTask(Task):
    def execute(self, *args, **kwargs):
        logging.info("Reversing the list")
        self._lst = ReverseListTask.reverse(self._lst)

    @staticmethod
    def reverse(lst: LinkedList):
        prev: Optional[Node] = None
        current: Node = lst.head
        while current is not None:
            next = current.next
            current.next = prev
            prev = current
            current = next
        lst.head = prev
        return lst

class PrintListTask(Task):
    def execute(self, *args, **kwargs):
        print("the list is")
        print(self._lst)
```

You can see that I moved the `reverse` method into `ReverseListTask`, so we can remove the method from the `LinkedList` class. One benefit of this task-based approach is that the logic that we want to perform is located within the `Task`, and this helps us achieve that task. None of the other `Task`s need to know about reversing a list, and having code around to do unnecessary tasks might become step towards "Dependency Hell."

Our yaml config has an `action` field that we can use to decide which of these subclasses to use for each step in the pipeline. Let's use a factory function for that <sup id="a1">[1](#f1)</sup>.

```python
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
```

Now it's time to think about parsing the yaml config itself. We'll put each `task` in the yaml array into a `TaskDefinition` dataclass to hold all of the parameters and values:

```python
from dataclasses import dataclass, field

@dataclass
class TaskDefinition:
    """
    Converts a task from the yaml config into a dataclass.

    Required fields are `name` and `action`. All other key -> value pairs listed in the yaml file will be passed to a `params` dict.
    """
    name: str
    action: str
    params: dict = field(default_factory=dict)

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

        return TaskDefinition(name=d["name"], action=d["action"], params=params)
```

At this point, we have

- Broken each step of the pipeline into a "task," which is described by a `TaskDefinition`.
- Made an abstract `Task` class that can be extended to perform the actual work defined by each stage of the pipeline.
- Made a helper function to convert an `action` (string) from the `TaskDefinition` into the appropriate `Task`.

Now we can write a `Parser` class to read the whole yaml file and turn it into a list of `TaskDefinitions` that we'll need to run. It will have three methods:

- `parse` to read the yaml and produce a list of `TaskDefinition`s
- `describe` to print a preview of which tasks will be executed
- `run` to create each `Task` in the pipeline and call `execute` on it

```python
import logging
import yaml
from typing import List, Optional
from tasks import task_factory, Task

class Parser:
    """
    Parses the pipeline yaml into a list of TaksDefinitions, and provides methods to describe and ultimately execute the pipeline.
    """

    def __init__(self, path: str):
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
```

Now when we execute `parser.py` we'll do this:

```python
if __name__ == "__main__":
    p = Parser("pipeline.yaml")
    p.parse()
    p.describe()
    p.run()
```

And we get the expected output:

```
$ python pipeline.py

~~ Tasks that will execute ~~
push_values - populate the list - {'elements': [1, 2, 3, 4]}
print_list - print the list - {}
reverse_list - reverse the list - {}
print_list - print the reversed list - {}
INFO:root:~~~
INFO:root:Populating the list with: [1, 2, 3, 4]
INFO:root:~~~
the list is
4, 3, 2, 1
INFO:root:~~~
INFO:root:Reversing the list
INFO:root:~~~
the list is
1, 2, 3, 4
```

We did it! We reversed a linked list. Want to add [some other task for a `LinkedList`](https://www.geeksforgeeks.org/top-20-linked-list-interview-question/)? No problem, we just have to:

- Define a new `action` for the yaml config.
- Extend `Task` with a new subclass and implement `execute`.
- Write some unit & integration tests, which are glaringly absent from this post!
- Add a line to `task_factory` to produce the new class for the appropriate value of `action`.
- Document it and communicate it to the users of your platform.

## The twist

Most coding interviews have a secret second phase. If a candidate solves the problem with lots of time to spare, we can ask an add-on question. Is this fair? Probably not. If a candidate can pass the interview by solving just the first part, they shouldn't be able to fail it by attempting the second. Hopefully by solving the second part of the question, they considered for a higher title.

In this case, we could make a more complex task execution graph. The execution graph looks like this in v1.

```
push_values -> print_list -> reverse_list -> print_list
```

The first `print_list` task and the `reverse_list` tasks are really operating on the same input (`print_list` is really just a side effect). We could allow each task to specify its parent and re-draw the graph to look like this.

```
               / -> print_values
              /
push_values -
              \
               \ -> reverse_list -> print_values
```

So we can change the yaml config format a bit to include an `id` for each task and a `parent` indicating the ID of upstream task. The new config will look like this. It's a breaking change, so we've moved to `apiVersion: 2`.

```yaml
apiVersion: 2
tasks:
  - name: "populate the list"
    id: 1
    action: push_values
    config:
      elements:
        - 1
        - 2
        - 3
        - 4
      demo_sleep_time: 1
  - name: "print the list"
    action: print_list
    id: 2
    parent: 1
    config:
      demo_sleep_time: 4
  - name: "reverse the list"
    action: reverse_list
    id: 3
    parent: 1
    config:
      demo_sleep_time: 2
  - name: "reverse the list a second time"
    action: reverse_list
    id: 5
    parent: 3
    config:
      demo_sleep_time: 2
  - name: "print the double reversed list"
    action: print_list
    id: 6
    parent: 5
    config:
      demo_sleep_time: 2
  - name: "print the single reversed list"
    action: print_list
    id: 4
    parent: 3
    config:
      demo_sleep_time: 1
```

Now we can implement a `Parser2` that's a little more advanced. Rather than a `List[Task]` we'll create a dictionary from `task_id -> List[downstream Tasks]`, and step through all of the tasks. Here's how `run` is implemented now (see the link at the bottom for the full code):

```python
class Parser2:
    def __init__(self, path):
        self.pipeline: dict = yaml.safe_load(open(path))
        self.task_definitions: Dict[int, TaskDefinition] = {}
        self.graph: Dict[int, List[TaskDefinition]] = defaultdict(list)

    def run_task(self, task_id: Optional[int], input_ll: LinkedList, visited: Set[int]):
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
                # the LinkedList within each task, so we deepcopy.
                ll = copy.deepcopy(parent_task.linked_list)
                self.run_task(child_task.id, ll, visited)

    def run(self):
        first_task_id = self.graph[None][0].id
        self.run_task(first_task_id, LinkedList(), set([]))
```

I made a _graph_ of parent and child tasks, and then step through starting at the head and hitting every child, passing the output of the parent to each of its children tasks. **It's a depth-first graph traversal** just hiding there right in front of us!

<!-- ## Appendix: advantages / disadvantages of the pipeline framework

Here are some advantages that I see to breaking work up like this.

1. By abstracting the implementation away from the user, we, the infra/platform team, are able to provide an easy human-readable interface that requires little to no code.
2. We are able to move the work of each task into its own self-contained _component_ (in practice, this usually means a Docker container).
3. Since all logic is "component-ized," we can execute the tasks in various environments - from local execution to a fully distributed computing environment - depending on the resources required.
4. Each component can come with its own `requirements.txt` file (or equivalent) which will help a bit with incompatible dependencies. In fact, there's no real reason all of the components even need to be in the same programming language!
5. We can submit these tasks to various schedulers to be executed, and swap them on the backend if needed (eg migrating from Airflow to Argo or similar).

There is an implied separation of execution from definition of the tasks to be performed - both technically and _organizationally_. This is a common thing at most large tech companies who split into Infrastructure and Product organizations. It's also key to industry trends such as [data mesh](https://towardsdatascience.com/what-is-a-data-mesh-and-how-not-to-mesh-it-up-210710bb41e0), which breaks data engineering tasks into three components: "data sources, data infrastructure, and domain-oriented data pipelines managed by functional owners."

In this case, the code that executes these tasks will be owned and maintained by a _patform_ or _infrastructure team_, and the yaml will be owned by a _product team_ that uses the provided platform.

## Let's talk about the downsides

There are some disadvantages to an approach like this as well. The above list of steps to add any new functionality can be pretty cumbersome, and it is all modifying code that we said is owned by the platform team. It will also likely require asking engineers to upgrade to the latest package version in order to get the newest functionality.

The biggest issue is that there currently isn't a way for a product team to implement their own `Task` logic (because the `task_factory` needs to be able to parse it), meaning everything needs to be committed to the platform team's repo. With that comes the need for the platform team to review PRs that contain business logic, product teams are blocked by the platform's release cycles (or, more likely, teams will start using dev/snapshot releases in production), and all kinds of other headaches.

Teams will also likely only upgrade when they _need_ the new functionality, meaning you'll always have teams running older versions of your platform. It's likely that the teams/projects that are reluctant to update to the latest version are the ones with the more stable and critical systems. You need to make sure that changes are backwards compatible. -->

## Wrap-up

Software interviews will continue to be hard forever. I could have asked [any number of questions](https://leetcode.com/tag/depth-first-search/) that require implementing a DFS - why go through all of these hoops with pipelines and tasks? Because workflow engines like Airflow, Prefect, Dagster, Luigi, etc are things that we use day-to-day, and we should have enough familiarity with them that we can implement a rudimentary version in the span of a 1-hour interview. It demonstrates that we can code, that we have a good understanding of one of our most common tools, and that we can even bust out the ol' graph traversal algorithm when we actually need to use it.

<b id="f1">1</b> A factory! In Python!? They're out there, folks. [↩](#a1)
