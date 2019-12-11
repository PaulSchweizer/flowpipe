# Flowpipe for VFX Pipelines

Flowpipe was inspired by commonly experienced challenges in vfx/animation pipelines.

**Re-usability**

Flowpipe encourages the re-usability of code through encapsualation into nodes that do just one thing. [Code example](examples/house_and_birthday.py)!

**Code Design in a 1000+ ways**

Usually a pipeline codebase tends to be organized in as many ways as the number of developers ever employed by the company. Every situation has a mutlitude of possible solutions and if there is no common framework and not enough structure every developer will pick whatever feels right to them.
Flowpipe helps by providing this very simple framework. Developers will be able to understand each other's code better and faster and can collaborate more easily.

**Planning and Coordination**

Thinking about the seolution to a problem in a graph-like fashion is a helpful approach in a lot of situations.
Since flowpipe naturally supports this approach, the planning phase can oftentimes be mapped more or less directly to a flowpipe graph. This helps to reason about the implementation, not only with other developers but also with non-technical people!

**Render Farm**

Usually any code that has to run on a render farm is wrapped individually with some help from the farm API itself and some in-house functionality. This means that the render farm leaves an imprint everywhere in the code base. It also means that getting things to run on the farm is usually a tedious process requiring custom code every time.
This is where flowpipe can really make a difference through the abstraction of logic into a graph which can then be translated into a farm job network in a unified way and thus avoiding all these issues.
Please see the detailed explanation below and the code examples on [vfx_render_farm_conversion.py](examples/vfx_render_farm_conversion.py)!

## Workflow Design Pattern

As the name suggests, this pattern wants to represent workflows. It is basically an extension of the 'Command Pattern' meant for more complex, long-running commands consisting of multiple sub-commands. Workflows also provide multiple ways of evaluation, usually local and remote (farm).

A workflow would be a common, pre-defined set of tasks frequently used in a pipeline, for example:

    * prepare a delivery to the client
    * publish geometry with a subsequent turntable rendering
    * ingest data from vendors, including data cleanup and transformation

The Workflow builds a Graph and initializes it with user provided settings as well as data taken from other sources (database, filesystem).

Refer to the [workflow_design_pattern.py](examples/workflow_design_pattern.py)! for an implementation example.

This can be a powerful approach, especially when used with the Farm Conversion.

```c
+--------------------------+          +--------------------------------+          +----------------------+
|         Publish          |          |        CreateTurntable         |          |    UpdateDatabase    |
|--------------------------|          |--------------------------------|          |----------------------|
o source_file<"model.ma">  |     +--->o alembic_cache<>                |          o asset<"model">       |
|           published_file o-----+    o render_template<"template.>    |     +--->o images<>             |
+--------------------------+     |    |                      turntable o-----+    o status<"published>   |
                                 |    +--------------------------------+          |                asset o
                                 |    +----------------------------------+        +----------------------+
                                 |    |           SendMessage            |
                                 |    |----------------------------------|
                                 |    o recipients<>                     |
                                 |    o template<"Hello,\n\>             |
                                 |    % values                           |
                                 +--->o  values.path<>                   |
                                      o  values.recipients<["john@mai>   |
                                      o  values.sender<"sender">         |
                                      |                    return_status o
                                      +----------------------------------+
```

## Farm Conversion

Since workflows rely on Flowpipe graphs they can be converted into a farm job of equal shape through this single entry point.

Every node is converted into a farm task. The flowpipe connections are used to determine the farm task dependencies.
Each node gets serialized to json and stored in a "database" before submission. On the farm, the node gets deserialized from there, with any upstream data also taken from the json "database". After evaluation, the node gets serialized back into the database, making the outputs available for the subsequent nodes.

There are three basic utilities required for this approach:

1. Convert a Graph to an equivalent farm job
2. Evaluate a Node on the farm
3. Handling the data transferral between nodes on the farm

Any farm specific settings are stored in the metadata of the nodes and/or directly provided on job creation.

Refer to [vfx_render_farm_conversion.py](examples/vfx_render_farm_conversion.py)! for a pseudo-implementation of all the required parts and [vfx_rendering.py](examples/vfx_rendering.py)! for an example of a complex graph.
It also touches on more complex concepts like implicit and explicit batching.
