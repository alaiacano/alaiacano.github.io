---
layout: post
title: "Developing Data Pipelines"
date: 2020-11-27 20:18:32 -0500
categories: data-engineering
---

Someone at work recently asked for some tips on developing data pipelines. These are the sorts of Big Data jobs that we write in [Scio](https://www.github.com/spotify/scio) but you might also use (py)spark, scalding, or some other Map/Reduce style framework. I wrote a few tips that I thought might be worth sharing. Some of these are scio-specific, but most of the ideas should generalize[^1].

The original question was coming from someone used to using python/jupyter for data manipulation, and was looking for tips in transitioning from a "quick iteration" development process to a "wait this takes _how long_ to run?" development process. Submitting jobs takes time, processing lots of data takes time (and money), inspecting results requires hunting down storage locations in some cloud storage bucket, errors are opaque and might take a long time to materialize.

So here are some tips I've found useful to shorten the iteration cycle.

### Lean on types

Without sparking a flame war, I've found that scala's type system & compiler are helpful when writing code. You know that things will _probably_ run reasonably well if it compiles. Python is perfectly happy sending strings to functions that expect integers, even if you have type hints. Scala will break on that and the IDE (intellij is king) helps a lot. That doesn't mean there aren't logical errors or the elusive `RuntimeException` in there!

You often have a lot of chained operations in a data pipeline. For example, say you have a data set with all of the city populations in the world and want to get all of the state populations within the US.

```scala
case class City(country: String, province: String, city: String, population: Int)

// sc.parallelize puts a manually-defined List into an SCollection
val cities :SCollection[City] = sc.parallelize(List(
  City("US", "Massachusetts", "Boston", 694583),
  City("US", "New York", "New York", 8399000),
  City("FR", "Ile de France", "Paris", 2161000)
  // ...and all of the rest of the cities
))

val statePopulations: SCollection[?????] = cities
  .filter { row => row.country == "US" }          // SCollection[City]
  .map { row => (row.province, row.population) }  // SCollection[(String, Int)]
  .sumByKey                                       // SCollection[(String, Int)]
```

IDEs like intellij or vscode (with scala metals) will tell you what type of data is inside of your SCollection at each step in the chain. Some plugins will even show you the type

### Tests and debugger

You don't have to write formal tests _first_, but they certainly can be helpful if you're stuck figuring something out. Scio has a `JobTest` class for tests and other frameworks have equivalents for:

- Specifying input data
- Passing any `arg`s to the job (this is typically how you specify input/output paths)
- Checking that the output matches expectations

You can run the test using an IDE debugger and place breakpoints in the scio job to make sure the values are what you expect at various points in the pipeline. This is probably going to be most similar to the iterative experience in a jupyter notebook, but setting up all of the mocked test data can be annoying (especially if your input data is a complex format with lots of embedded records). For good, reliable code you'll write these tests eventually anyway!

### Use a lot of counters.

There are different types of [counters](https://spotify.github.io/scio/examples/MetricsExample.scala.html) that you can increment on certain conditions to make sure you do/don't see what you are looking for.

For long-term monitoring of data quality, these counters (Hadoop and Spark have similar concepts) can be recorded and monitored. At Spotify, we have a service that can send Pagerduty alerts if certain counter thresholds are not met.

### Use the Dataflow graph

This one is related to counters and a bit Dataflow-specific. You can click on any node in the Dataflow graph when it is running and see the number of input and output elements. For example, if you're doing an innerJoin and you see `X` input records from one SCollection and `Y` input records from the other, you should see `X (union on key) Y` output records. You probably have some intuition of what that number should be, and can confirm it in the job execution UI. If you don't see what you expect, something could be wrong in the join. This also applies to `filter` or `flatMap` functions, and many more.

In scio, you can also use `.withName("a description of this step")` on any SCollection. So for example:

```scala
sc.parallelize(List(1,2,3,4,5,6,7))
  .filter(e => e % 2 == 0)
  .withName("remove odd values")
  .map( ... the next thing ...)
```

The filter node in the Dataflow graph will have your supplied name, and you'd expect that the number of output elements should be about half as much as the input.

### Output to Bigquery

I always save a copy of my result to BQ when developing pipelines, even if it eventually stores its output in a different format. It lets you visually inspect it and do all of the tricks you're used to doing via SQL. You can use [`@BigQueryType.toTable`](https://spotify.github.io/scio/io/Type-Safe-BigQuery.html#bigquerytype-totable) to annotate any scala case class and then [save it as a BQ table](https://spotify.github.io/scio/io/Type-Safe-BigQuery.html#type-safe-bigquery-with-scio)

I have seen some implementations of a `bqTap` function that will take snapshots of an SCollection at various points. The use looks like this:

```scala
sc.parallelize(List(1,2,3,4,5,6,7))
  .filter(e => e % 2 == 0)
  .bqTap("my-project:my-dataset.evens_only")
  .map( ... the next thing ...)
```

Just be careful not to store decrypted PII in your debugging!

### Run on a subset of data

If you can limit the amount of data read or processed (either by filtering, or processing one day’s worth of data instead of multiple, etc) that will speed up the iteration process.

[^1]: TLDR for people familiar with at least one of these: Scio/`SCollection` == Spark/`RDD` == Scalding/`TypedPipe`.
