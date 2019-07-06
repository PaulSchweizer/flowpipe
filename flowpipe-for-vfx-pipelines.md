# Flowpipe for VFX and Animation Pipelines aka the Workflow Design Pattern

Flowpipe was inspired by commonly experienced problems in vfx/animation pipelines.

**Re-usability**

Flowpipe encourages the re-usability of code through the encapsualation into nodes. The amount of re-usability is in the end down to the developers implementing the nodes.

**Code Design in a 1000+ ways**

Usually a pipeline codebase tends to be organized in as many ways as the number of developers ever employed by the company. Every situation has a mutlitude of possible solutions and if there is no common framework and not enough structure every developer will pick whatever feels right to them.
Flowpipe helps in this way as it provides this very simple framework. Developers will be able to understand each other's code better and faster and can collaborate more easily.

**Planning and Coordination**

Thinking about the problem in a graph-like fashion is often a helfpul approach to solving the problem.
Since flowpipe naturally supports this approach, the planning phase can oftentimes be mapped more or less direclty to a flowpipe node network. This saves time and keeps the planning phase directly in line with the implementation.

**Render Farm**

Usually any code that has to run on the render farm is wrapped individually with some help from the farm api itself and some in-house functionality. This means that the render farm leaves an imprint everywhere in the code base. It also means that running things on the farm is usually a tedious process.
This is where flowpipe can really make a difference as it abstracts the logic of a problem into a node network which can then be translated into a farm job network in a unified way.
This approach has been successfully implemented at two vfx studios so far.

## Workflow Design Pattern

As the name suggests, this pattern wants to represent workflows. A workflow would be a common, pre-defined set of tasks frequently used in a pipeline, for example a delivery to the client, a geometry publish with a subsequent turn table rendering or a vendor ingestion, including data cleanup and transformation.

The Workflow builds a Graph and initializes it with user provided settings as well as other initial values necessary to get the workflow initialized.

Consider this "Publish Workflow with Turntable" as an example:

```python

from flowpipe.graph import Graph
from flowpipe.node import Node


@Node(outputs=["published_file"])
def Publish(source_file):
    """Publish the given source file."""
    return {"published_file": "/published/file.abc"}


@Node(outputs=["turntable"])
def CreateTurntable(alembic_cache, render_template):
    """Load the given cache into the given template file and create a render."""
    return {"turntable": "/turntable/turntable.jpg"}


@Node(outputs=["status"])
def UpdateDatabase(asset, images, status):
    """Update the database entries of the given asset with the given data."""
    return {"status": True}


class PublishWorkflow:
    """Publish a model and add a turntable render of it to the database."""

    def __init__(self, source_file):
        # Create the graph
        self.graph = Graph()
        publish = Publish(graph=self.graph)
        turntable = CreateTurntable(graph=self.graph)
        update = UpdateDatabase(graph=self.graph)
        publish.outputs["published_file"].connect(turntable.inputs["alembic_cache"])
        turntable.outputs["turntable"].connect(update.inputs["images"])

        # Initialize the graph from user input
        publish.inputs["source_file"].value = source_file

        # Initialize the graph through pipeline logic
        # These things can also be done in the nodes themselves of course, it's a design choice and depends on the case
        render_template = "/{project}/templates/turntable_template.ma".format(project="PROJECT")
        turntable.inputs["render_template"].value = render_template
        update.inputs["asset"].value = source_file.split(".")[0]


workflow = PublishWorkflow("model.ma")
print(workflow.graph)

```

The workflow preview looks like this:

```

+------------------------+          +------------------------------+          +-------------------+
|        Publish         |          |       CreateTurntable        |          |  UpdateDatabase   |
|------------------------|          |------------------------------|          |-------------------|
o source_file<"model.ma">|     +--->o alembic_cache<>              |          o asset<"model">    |
|         published_file o-----+    o render_template<"/PROJECT/>  |     +--->o images<>          |
+------------------------+          |                    turntable o-----+    o status<>          |
                                    +------------------------------+          |            status o
                                                                              +-------------------+

```

### Farm Submission

The workflow can now be converted into a farm job of equal shape.

Every node is converted into a farm task. The flowpipe connections are used to determine the farm task dependencies.
Each node gets serialized to json and stored in a "database" before submission. On the farm, the node gets deserialized from there,  with any upstream data also taken from the json "database". After evaluation, the node gets serialized back into the database, making the outputs available for the subsequent nodes.

There are three basic utilities required for this approach:

1. Convert a Graph to an equivalent farm job
2. Evaluate a Node on the farm
3. Handling the data transferral between nodes on the farm

Any farm specific settings are stored in the metadata of the nodes and/or directly provided on job creation.

The following pseudo implementation demonstrates the concept:

```python

import json


class JsonDatabase:

    PATH = "~/Desktop/json-database/{identifier}.json"

    @staticmethod
    def set(node):
        serialized_json = JsonDatabase.PATH.format(identifier=node.identifier)
        with open(serialized_json, "w") as f:
            json.dump(node.serialize(), f, indent=2)
        return serialized_json

    @staticmethod
    def get(identifier):
        serialized_json = JsonDatabase.PATH.format(identifier=identifier)
        with open(serialized_json, "r") as f:
            data = json.load(f)
        return INode.deserialize(data)


COMMANDS = {
    "python": (
        "python -c '"
        "from my_farm import conversion;"
        "conversion.evaluate_on_farm(\"{serialized_json}\")'"),
    "maya": (
        "mayapy -c '"
        "import maya.standalone;"
        "maya.standalone.initialize(name=\"python\");"
        "from my_farm import conversion;"
        "conversion.evaluate_on_farm(\"{serialized_json}\")'")
}


def convert_graph_to_job(graph):
    job = {
        "name": graph.name,
        "tasks": []
    }

    # Farm Tasks
    #
    for node in graph.nodes:
        serialized_json = JsonDatabase.set(node)
        task = {
            "name": node.name
        }
        command = COMMANDS.get(node.metadata.get("interpreter", "python"), None)
        task["command"] = command.format(serialized_json=serialized_json)
        job["tasks"].append(task)

    # Dependencies
    #
    for node in graph.nodes:
        task = [t for t in job["tasks"] if t["name"] == node.name][0]
        task["dependencies"] = [n.name for n in node.upstream_nodes]
    return job


def evaluate_on_farm(serialized_json):
    # Debug logs might be useful on the farm
    #
    flowpipe.logger.setLevel(logging.DEBUG)

    # Deserialize the node from the serialized json
    #
    with open(serialized_json, "r") as f:
        data = json.load(f)
    node = INode.deserialize(data)

    # Retrieve the upstream output data
    #
    for name, input_plug in data["inputs"].items():
        for identifier, output_plug in input_plug["connections"].items():
            upstream_node = JsonDatabase.get(identifier)
            node.inputs[name].value = upstream_node.outputs[output_plug].value

    # Actually evalute the node
    #
    node.evaluate()

    # Store the result back into the same file
    #
    with open(serialized_json, "w") as f:
        json.dump(node.serialize(), f, indent=2)


job = convert_graph_to_job(workflow.graph)

print(json.dumps(job, indent=2))

```

This is what the job would look like:

```json

{
  "name": "Graph",
  "tasks": [
    {
      "dependencies": [],
      "command": "python -c 'from my_farm import conversion;conversion.evaluate_on_farm(\"~/Desktop/json-database/Publish-26b909f6-7d4b-451f-a1f3-42f98b94d6c1.json\")'",
      "name": "Publish"
    },
    {
      "dependencies": [
        "Publish"
      ],
      "command": "python -c 'from my_farm import conversion;conversion.evaluate_on_farm(\"~/Desktop/json-database/CreateTurntable-33bdefbc-58e4-49d3-9d59-3869013764b8.json\")'",
      "name": "CreateTurntable"
    },
    {
      "dependencies": [
        "CreateTurntable"
      ],
      "command": "python -c 'from my_farm import conversion;conversion.evaluate_on_farm(\"~/Desktop/json-database/UpdateDatabase-b1948094-eee8-4591-8b01-636f98362995.json\")'",
      "name": "UpdateDatabase"
    }
  ]
}

```

### Advanced Farm Concepts - Batching

Render farms usually support some sort of batching tasks into chunks. This can be implemented in flowpipe as well.

Each batchable node has to have a dedicated input for the batch frames/numbers, just define a convention for your studio.
**Make sure to work with abstract frame range notations here, otheriwse the subsequent node will only pick up a part of the images!**
The batch size should go into the metadata of the node.

```python

@Node(outputs=["renderings"])
def Render(frames, scene_file):
    return {"rendering": "/renderings/file.%04d.exr"}

render = Render(frames=range(100), scene_file="/scene/for/rendering.ma", metadata={"batch_size": 10})

```

Farm conversion and evaluation on the farm would then have to take the batching into account.

**Every render farm handles batched task creation differently, so this example is mainly an inspiration for how batching could be implemented!**

```python

# The commands have to account for the batched frames
#
COMMANDS = {
    "python": (
        "python -c '"
        "from my_farm import conversion;"
        "conversion.evaluate_on_farm(\"{serialized_json}\", frames={frames})'")
}


def convert_graph_to_job(graph):
    job = {
        "name": graph.name,
        "tasks": []
    }

    # Farm Tasks
    #
    tasks = {}
    for node in graph.nodes:
        serialized_json = JsonDatabase.set(node)

        tasks[node.name] = []

        # Create individual tasks for each batch if the batch size was defined
        #
        if node.metadata.get("batch_size") is not None:
            batch_size = node.metadata["batch_size"]
            frames = node.inputs["frames"].value
            i = 0
            while i < len(frames) - 1:
                end = i + batch_size
                if end  > len(frames) - 1:
                    end = len(frames)
                f = frames[i:end]

                task = {
                    "name": "{0}-{1}".format(node.name, i / batch_size)
                }
                command = COMMANDS.get(node.metadata.get("interpreter", "python"), None)
                task["command"] = command.format(serialized_json=serialized_json, frames=f)
                job["tasks"].append(task)

                tasks[node.name].append(task)

                i += batch_size
        else:
            task = {
                "name": node.name
            }
            command = COMMANDS.get(node.metadata.get("interpreter", "python"), None)
            task["command"] = command.format(serialized_json=serialized_json, frames=None)
            job["tasks"].append(task)

            tasks[node.name].append(task)

    # Dependencies
    #
    for node_name in tasks:
        for task in tasks[node_name]:
            node = graph[node_name]
            task["dependencies"] = []
            for upstream in [n.name for n in node.upstream_nodes]:
                task["dependencies"] += [t["name"] for t in tasks[upstream]]

    return job


def evaluate_on_farm(serialized_json, frames=None):
    # Debug logs might be useful on the farm
    #
    flowpipe.logger.setLevel(logging.DEBUG)

    # Deserialize the node from the serialized json
    #
    with open(serialized_json, "r") as f:
        data = json.load(f)
    node = INode.deserialize(data)

    # Retrieve the upstream output data
    #
    for name, input_plug in data["inputs"].items():
        for identifier, output_plug in input_plug["connections"].items():
            upstream_node = JsonDatabase.get(identifier)
            node.inputs[name].value = upstream_node.outputs[output_plug].value

    # Specifically assign the batch frames here if applicable
    #
    if frames is not None:
        all_frames = node.inputs["frames"]
        node.inputs["frames"] = frames

    # Actually evalute the node
    #
    node.evaluate()

    # Store the result back into the same file ONLY once
    # ALL batch processes access the same json file so the result is only stored
    # for the last batch, knowing that the last batch in numbers might not be
    # the last batch actually executed
    #
    if frames is not None and frames[-1] != all_frames[-1]:
        return

    with open(serialized_json, "w") as f:
        json.dump(node.serialize(), f, indent=2)


@Node(outputs=["renderings"])
def Render(frames, scene_file):
    return {"rendering": "/renderings/file.%04d.exr"}


@Node(outputs=["status"])
def UpdateDatabase(asset, images, status):
    """Update the database entries of the given asset with the given data."""
    return {"status": True}


graph = Graph(name="Rendering")
render = Render(graph=graph, frames=range(30), scene_file="/scene/for/rendering.ma", metadata={"batch_size": 10})
update = UpdateDatabase(graph=graph)
render.outputs["renderings"].connect(update.inputs["images"])

print(graph)
print(json.dumps(convert_graph_to_job(graph), indent=2))

```

```

+-------------------------+          +-------------------+
|         Render          |          |  UpdateDatabase   |
|-------------------------|          |-------------------|
o frames<[0, 1, 2, >      |          o asset<>           |
o scene_file<"/scene/fo>  |     +--->o images<>          |
|              renderings o-----+    o status<>          |
+-------------------------+          |            status o
                                     +-------------------+


```

The resulting job looks like this:

```json

{
  "name": "Rendering",
  "tasks": [
    {
      "dependencies": [],
      "command": "python -c 'from my_farm import conversion;conversion.evaluate_on_farm(\"~/Desktop/json-database/Render-200be6d3-7654-4567-9a27-cdc21b274143.json\", frames=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])'",
      "name": "Render-0"
    },
    {
      "dependencies": [],
      "command": "python -c 'from my_farm import conversion;conversion.evaluate_on_farm(\"~/Desktop/json-database/Render-200be6d3-7654-4567-9a27-cdc21b274143.json\", frames=[10, 11, 12, 13, 14, 15, 16, 17, 18, 19])'",
      "name": "Render-1"
    },
    {
      "dependencies": [],
      "command": "python -c 'from my_farm import conversion;conversion.evaluate_on_farm(\"~/Desktop/json-database/Render-200be6d3-7654-4567-9a27-cdc21b274143.json\", frames=[20, 21, 22, 23, 24, 25, 26, 27, 28, 29])'",
      "name": "Render-2"
    },
    {
      "dependencies": [
        "Render"
      ],
      "command": "python -c 'from my_farm import conversion;conversion.evaluate_on_farm(\"~/Desktop/json-database/UpdateDatabase-84918a87-8eaa-4659-ab93-21fc2099e4cf.json\", frames=None)'",
      "name": "UpdateDatabase"
    }
  ]
}

```
