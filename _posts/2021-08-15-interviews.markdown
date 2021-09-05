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

The programming interview is probably the most hated. I personally don't like being on either side of these interviews. Leetcode-style problems that test _CS fundamentals_ can be fun puzzles for some people, and are arguably a decent evaluation of junior engineers without industry experience, but it's a [common](https://twitter.com/PhDemetri/status/1425579904205299721) [complaint](https://twitter.com/CubicleApril/status/1424011476889702402) among [senior engineers](https://twitter.com/andrew_n_carr/status/1341837026191011842) that they have to study material that they haven't used in years to get a job where they won't use it. I've certainly come out of interviews tempted to ask "Is this the sort of thing your engineers actually do?" This tweet, from the author of [Homebrew](https://brew.sh/), lives in infamy.

<blockquote class="twitter-tweet" data-dnt="true" data-theme="dark"><p lang="en" dir="ltr">Google: 90% of our engineers use the software you wrote (Homebrew), but you can’t invert a binary tree on a whiteboard so fuck off.</p>&mdash; Max Howell (@mxcl) <a href="https://twitter.com/mxcl/status/608682016205344768?ref_src=twsrc%5Etfw">June 10, 2015</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

There are a few questions that people like to use as punching bags. Invert a binary tree. Reverse a linked list. Perform breadth-first and/or depth-first tree traversals. Anything to do with heaps. I recently read the [history of the "Reverse A Linked List" problem](https://www.hillelwayne.com/post/linked-lists/) and find this take fascintating. The goal wasn't to reverse a linked list, it was to make sure you are familiar with pointer manipulation in C, and reversing the linked list was a good way to demonstrate that.

> In the early 80’s, C programmers were in high demand. Interviewers used questions that specifically tested your experience with C, which meant problems involving lots of pointer manipulation. This ingrained LL questions as a cultural institution in many places, especially places doing lots of low-level work, like Microsoft and Google. From there, it was exported to the wider software world, and lacking the original context, people assumed it was about “testing CS fundamentals” or “quick thinking”.

The fact remains that it's an important part of an interview to make sure that a software engineer can code. So if we're going to be asked to reverse a linked list, what is the real underlying assessment? In 2021, that is probably no longer about pointer manipulation. What should it be about, then? Let's dig in and have some fun.

## Reversing a Linked List

We'll start with the classic algorithm question. My solution is [here](https://gist.github.com/alaiacano/35a63e7631b60641fc0342f31461b80d#file-ll-py). Inserting new nodes at the head of the list is `O(1)` and reversing the list is `O(N)`, and does so by moving pointers around and not making a full copy of the list in memory.

To populate, print, reverse, and then print the list again, we'd do this:

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=run_ll.py" type="text/javascript"></script>

Wonderful. In the real world, we would have used [`List.reverse`](https://github.com/python/cpython/blob/e5c8ddb1714fb51ab1defa24352c98e0f01205dc/Objects/listobject.c#L1042-L1056) from the standard library, but this produces the same result. Would we have run the code in a module like this? Probably not!

## Enter the LinkedList Pipeline

Let's rewrite how we use this `LinkedList` class into something a little more _modern_:

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=pipeline1.yaml" type="text/javascript"></script>

YAML! Nice. YAML is fun to joke about, but Vicki Boykis posted [a twitter poll](https://twitter.com/vboykis/status/1407821631997759488) about which languages people use in Data Science/ML and the most common reply was "does YAML count?" If everyone asks, it means yes.

The above YAML does not actually do anything, and this is ostensibly a post about software coding interviews, so let's build something that reverses a linked list given this pipeline definition. Is this overkill for the goal of reversing a 4-element linked list? Sure. But it's a good analog to the modular systems that we are paid to build and use as software engineers, especially Data/ML engineers.

It is increasingly common to use this kind of "pipeline-as-YAML" configuration to piece together a workflow of pre-built components <sup id="a1">[1](#f1)</sup>. Some real examples of this are [TFX components](https://www.tensorflow.org/tfx/guide/understanding_tfx_pipelines#component), [scikit-learn Pipelines](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html), or [Airflow DAGs](https://airflow.apache.org/docs/apache-airflow/1.10.12/concepts.html). Perhaps _components_ are the new _pointers_. If that's the case, let's make a coding question that will use this context to assess coding ability.

### Coding problem: Implement a framework to execute this pipeline

First we'll need to define a `Task` class to carry out the logic of each `task` defined in the YAML. A `Task` may take an input `LinkedList` from a previous `Task`, performs some operation on it, and produces an output. Here's the interface:

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=base_task.py" type="text/javascript"></script>

It takes an input `LinkedList` and a `name` for the task, and has an abstract `execute` method that will have to mutate `self._lst`. As an interviewer, I'd ask whether mutating `self._lst` is ideal here. "Pipelines" are a pretty functional concept, where side effects are not ideal. How would the candidate account for this mutation and make sure it's safe? This is a great opportunity for a conversation about ways of building software, which you don't really get when the problem is to implement a single algorithm.

With that, let's extend `Task` to perform the actions seen in the YAML: `push_values`, `reverse_list`, and `print_list`.

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=tasks.py" type="text/javascript"></script>

You can see that I moved the `reverse` method into `ReverseListTask`, so we can remove the method from the `LinkedList` class. One benefit of this task-based approach is that the logic that we want to perform is located within the `Task`, and this helps us achieve that task. None of the other `Task`s need to know about reversing a list, and having code around to do unnecessary tasks might become step towards "Dependency Hell."

Our YAML config has an `action` field that we can use to decide which of these subclasses to use for each step in the pipeline. Let's use a factory function for that <sup id="a2">[2](#f2)</sup>.

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=task_factory.py" type="text/javascript"></script>

Now it's time to think about parsing the YAML config itself. We'll put each `task` in the YAML array into a `TaskDefinition` dataclass to hold all of the parameters and values:

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=task_definition.py" type="text/javascript"></script>

At this point, we have:

- Broken each step of the pipeline into a "task," which is described by a `TaskDefinition`.
- Made an abstract `Task` class that can be extended to perform the actual work defined by each stage of the pipeline.
- Made a helper function to convert an `action` (string) from the `TaskDefinition` into the appropriate `Task`.

Now we can write a `Parser` class to read the whole YAML file and turn it into a list of `TaskDefinitions` that we'll need to run. It will have three methods:

- `parse` to read the YAML and produce a list of `TaskDefinition`s
- `describe` to print a preview of which tasks will be executed
- `run` to create each `Task` in the pipeline and call `execute` on it

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=parser.py" type="text/javascript"></script>

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

- Define a new `action` for the YAML config.
- Extend `Task` with a new subclass and implement `execute`.
- Write some unit & integration tests, which are glaringly absent from this post!
- Add a line to `task_factory` to produce the new class for the appropriate value of `action`.
- Document it and communicate it to the users of your platform.

## The twist

Most coding interviews have a secret second part. If a candidate solves the problem with lots of time to spare, we can ask an add-on question. Is this fair? Probably not. If a candidate can pass the interview by solving just the first part, they shouldn't be able to fail it by attempting the second. Hopefully by solving the second part of the question they considered for a higher title, and not penalized for getting stuck on it.

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

So we can change the YAML config format a bit to include an `id` for each task and a `parent` indicating the ID of upstream task. The new config will look like this. It's a breaking change, so we've moved to `apiVersion: 2`.

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=pipeline2.yaml" type="text/javascript"></script>

Now we can implement a `Parser2` that's a little more advanced. Rather than a `List[Task]` we'll create a dictionary from `task_id -> List[downstream Tasks]`, and step through all of the tasks. Here's how `run` is implemented now (see the link at the bottom for the full code):

<script src="https://gist.github.com/35a63e7631b60641fc0342f31461b80d.js?file=parser2.py" type="text/javascript"></script>

I made a _graph_ of parent and child tasks, and then step through starting at the head and hitting every child, passing the output of the parent to each of its children tasks. **It's a depth-first graph traversal** just hiding there right in front of us!

## Wrap-up

<blockquote class="twitter-tweet"><p lang="en" dir="ltr">All job interview processes are flawed. They&#39;re just flawed in different ways, and some of those flaws work to your advantage and some don&#39;t. That&#39;s it, that&#39;s the newsletter.</p>&mdash; Vicki Boykis (@vboykis) <a href="https://twitter.com/vboykis/status/1316019970032070661?ref_src=twsrc%5Etfw">October 13, 2020</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

The original quote that I shared suggested that asking a candidate to implement a specfic algorithm (reverse a linked list) was a vehicle for testing a broader set of knowledge (experience with writing in C). In my problem, we ask directly about the broader set of knowledge (familiarity with pipelines / DAGs), and reveal a situation where a specific algorithm needs to be used (graph traversal).

My task is far more life-like, putting the candidate in a familiar situation and likely less stressful state of mind. If the candidate asks if this is what your engineers really do, you can more confidently say "yes." There is also much more opportunity to discuss design approaches and trade-offs, and a chance at the end to speculate how it could be advanced further (Async tasks? Just use Airflow?).

I'll ask that you consider putting a little more effort into your programming questions than picking something straight from leetcode. It will be more enjoyable for both the interviewer and candidate, provide a better hiring signal, and allow you to base your hiring decision more on skill and experience than the candidate's luck.

---

<b id="f1">1</b> This idea is up for debate. Should programmers [build from scratch](https://cacm.acm.org/magazines/2008/8/5355-interview-donald-knuth-a-lifes-work-interrupted/fulltext), or stitch various services/components together (["VendorOps"](https://rachelbythebay.com/w/2020/08/14/jobs/))? I agree there's [room for both](https://twitter.com/drunkcod/status/1429422275535769606?s=21). I hope it's obvious that in this post I am focusing on the latter. [↩](#a1)

<b id="f2">2</b> A factory! In Python!? They're out there, folks. [↩](#a2)

Thanks to [Matt Brown](https://twitter.com/mattnworb) for feedback on this post.
