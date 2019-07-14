"""Demonstrating how to convert a flowpipe graph to a render farm job.

This guide expects that your render farm can handle dependencies between tasks.
"""
import json
import logging
import os
from tempfile import gettempdir

import flowpipe
from flowpipe.graph import Graph
from flowpipe.node import INode, Node


# -----------------------------------------------------------------------------
#
# Necessary utilities
#
# -----------------------------------------------------------------------------


class JsonDatabase:
    """The Database stores the JSON-serialized nodes.

    The storage can also be handled via a database, this is just the easiest
    way for demonstrational purposes. In production, a file based storage also
    has advantages for debugging and allows for easy hacking by just altering
    the JSON files directly.
    """

    PATH = os.path.join(gettempdir(), 'json-database', '{identifier}.json')

    @staticmethod
    def set(node):
        """Store the node under it's identifier."""
        serialized_json = JsonDatabase.PATH.format(identifier=node.identifier)
        if not os.path.exists(os.path.dirname(serialized_json)):
            os.makedirs(os.path.dirname(serialized_json))
        with open(serialized_json, 'w') as f:
            json.dump(node.serialize(), f, indent=2)
        return serialized_json

    @staticmethod
    def get(identifier):
        """Retrieve the node behind the given identifier."""
        serialized_json = JsonDatabase.PATH.format(identifier=identifier)
        with open(serialized_json, 'r') as f:
            data = json.load(f)
        return INode.deserialize(data)


# Command templates to execute a flowpipe node in the terminal.
# Uses different python interpreters and commands based on the host application
# The template just needs the path to the serialized json file and optionally
# a range of frames passed to the node for the implicit batch conversion.
COMMANDS = {
    "python": (
        "python -c '"
        "from my_farm import conversion;"
        "conversion.evaluate_on_farm(\"{serialized_json}\", {frames})'"),
    "maya": (
        "mayapy -c '"
        "import maya.standalone;"
        "maya.standalone.initialize(name=\"python\");"
        "from my_farm import conversion;"
        "conversion.evaluate_on_farm(\"{serialized_json}\", {frames})'")
}


def convert_graph_to_job(graph):
    """Convert the graph to a dict representing a typical render farm job."""
    job = {
        'name': graph.name,
        'tasks': []
    }

    # Turn every node into a farm task
    tasks = {}
    for node in graph.nodes:
        serialized_json = JsonDatabase.set(node)

        tasks[node.name] = []

        # IMPLICIT BATCHING:
        # Create individual tasks for each batch if the batch size is defined
        # Feed the calculated frame range to each batch
        if node.metadata.get('batch_size') is not None:
            batch_size = node.metadata['batch_size']
            frames = node.inputs['frames'].value
            i = 0
            while i < len(frames) - 1:
                end = i + batch_size
                if end  > len(frames) - 1:
                    end = len(frames)
                f = frames[i:end]

                task = {
                    'name': '{0}-{1}'.format(node.name, i / batch_size)
                }
                command = COMMANDS.get(node.metadata.get('interpreter', 'python'), None)
                task['command'] = command.format(serialized_json=serialized_json, frames=f)
                job['tasks'].append(task)

                tasks[node.name].append(task)

                i += batch_size
        else:
            task = {
                'name': node.name
            }
            command = COMMANDS.get(node.metadata.get('interpreter', 'python'), None)
            task['command'] = command.format(serialized_json=serialized_json, frames=None)
            job['tasks'].append(task)

            tasks[node.name].append(task)

    # The dependencies between the tasks based on the connections of the Nodes
    for node_name in tasks:
        for task in tasks[node_name]:
            node = graph[node_name]
            task['dependencies'] = []
            for upstream in [n.name for n in node.upstream_nodes]:
                task['dependencies'] += [t['name'] for t in tasks[upstream]]

    return job


def evaluate_on_farm(serialized_json, frames=None):
    """Evaluate the node behind the given json file.

    1. Deserialize the node
    2. Collect any input values from any upstream dependencies
        For implicit batching, the given frames are assigned to the node,
        overriding whatever might be stored in the json file, becuase all
        batches share the same json file.
    3. Evaluate the node
    4. Serialize the node back into its original file
        For implicit farm conversion, the serialization only happens once,
        for the 'last' batch, knowing that the last batch in numbers might
        not be the 'last' batch actually executed.
    """
    # Debug logs might be useful on the farm
    flowpipe.logger.setLevel(logging.DEBUG)

    # Deserialize the node from the serialized json
    with open(serialized_json, 'r') as f:
        data = json.load(f)
    node = INode.deserialize(data)

    # Retrieve the upstream output data
    for name, input_plug in data['inputs'].items():
        for identifier, output_plug in input_plug['connections'].items():
            upstream_node = JsonDatabase.get(identifier)
            node.inputs[name].value = upstream_node.outputs[output_plug].value

    # Specifically assign the batch frames here if applicable
    if frames is not None:
        all_frames = node.inputs['frames']
        node.inputs['frames'] = frames

    # Actually evalute the node
    node.evaluate()

    # Store the result back into the same file ONLY once
    # ALL batch processes access the same json file so the result is only stored
    # for the last batch, knowing that the last batch in numbers might not be
    # the last batch actually executed
    if frames is not None and frames[-1] != all_frames[-1]:
        return

    with open(serialized_json, 'w') as f:
        json.dump(node.serialize(), f, indent=2)


# -----------------------------------------------------------------------------
#
# Examples
#
# -----------------------------------------------------------------------------


@Node(outputs=['renderings'], metadata={'interpreter': 'maya'})
def MayaRender(frames, scene_file):
    """Render the given frames from the given scene.."""
    return {'renderings': '/renderings/file.%04d.exr'}


@Node(outputs=['status'])
def UpdateDatabase(id_, images):
    """Update the database entries of the given asset with the given data."""
    return {'status': True}


def implicit_batching(frames, batch_size):
    """Batches are created during the farm conversion."""
    graph = Graph(name='Rendering')
    render = MayaRender(
        graph=graph,
        frames=range(frames),
        scene_file='/scene/for/rendering.ma',
        metadata={'batch_size': batch_size})
    update = UpdateDatabase(graph=graph, id_=123456)
    render.outputs['renderings'].connect(update.inputs['images'])

    print(graph)
    print(json.dumps(convert_graph_to_job(graph), indent=2))


def explicit_batching(frames, batch_size):
    """Batches are already part of the graph."""
    graph = Graph(name='Rendering')
    update_database = UpdateDatabase(graph=graph, id_=123456)
    for i in range(0, frames, batch_size):
        maya_render = MayaRender(
            name='MayaRender{0}-{1}'.format(i, i + batch_size),
            graph=graph,
            frames=range(i, i + batch_size),
            scene_file='/scene/for/rendering.ma')
        maya_render.outputs['renderings'].connect(update_database.inputs['images'][str(i)])

    print(graph)
    print(json.dumps(convert_graph_to_job(graph), indent=2))


if __name__ == '__main__':
    implicit_batching(30, 10)
    explicit_batching(30, 10)
