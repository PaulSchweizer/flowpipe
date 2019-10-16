try:
    import importlib
except ImportError:
    pass
import imp
import json
from hashlib import sha256
import sys


def import_class(module, cls_name, file_location=None):
    """Import and return the given class from the given module.

    File location can be given to import the class from a location that
    is not accessible through the PYTHONPATH.
    This works from python 2.6 to python 3.
    """
    try:
        module = importlib.import_module(module)
    except NameError:  # pragma: no cover
        module = __import__(module, globals(), locals(), ['object'], -1)
    try:
        cls = getattr(module, cls_name)
    except AttributeError:  # pragma: no cover
        module = imp.load_source('module', file_location)
        cls = getattr(module, cls_name)
    return cls


def deserialize_node(data):
    """De-serialize a node from the given json data."""
    node = import_class(
        data['module'], data['cls'], data['file_location'])(graph=None)
    node.post_deserialize(data)
    return node


def deserialize_graph(data):
    """De-serialize from the given json data."""
    graph = import_class(data['module'], data['cls'])()
    graph._nodes = []
    for node in data['nodes']:
        graph._nodes.append(deserialize_node(node))
    nodes = {n.identifier: n for n in graph.nodes}
    for node in data['nodes']:
        this = nodes[node['identifier']]
        for name, input_ in node['inputs'].items():
            for identifier, plug in input_['connections'].items():
                upstream = nodes[identifier]
                upstream.outputs[plug] >> this.inputs[name]
            for sub_plug_name, sub_plug in input_['sub_plugs'].items():
                sub_plug_name = sub_plug_name.split('.')[-1]
                for identifier, plug in sub_plug['connections'].items():
                    upstream = nodes[identifier]
                    upstream.outputs[plug].connect(
                        this.inputs[name][sub_plug_name])
    return graph


class NodeEncoder(json.JSONEncoder):
    """Custom JSONEncoder to handle non-json serializable node values.

    If the value is not json serializable, a sha256 hash of its bytes is
    encoded instead.
    """

    def default(self, o):
        """Encode the object, handling type errors by encoding into sha256."""
        try:
            return super(NodeEncoder, self).default(o)
        except TypeError:
            try:
                return sha256(o).hexdigest()
            except TypeError:
                return str(o)
            except ValueError:
                return sha256(bytes(o)).hexdigest()


def get_hash(obj, hash_func=lambda x: sha256(x).hexdigest()):
    """Safely get the hash of an object.

    This function tries to compute the hash as safely as possible, dealing with
    json data and strings in a well-defined manner.

    Args:
        obj: The object to hash
        hash_func (func(obj) -> str): The hashing function to use

    Returns:
        (str): A hash of the obj

    """
    try:
        return hash_func(obj)
    except TypeError:
        try:
            js = json.dumps(obj, sort_keys=True)
        except TypeError:  # pragma: no cover
            pass
        else:
            obj = js
        if isinstance(obj, str):
            return hash_func(obj.encode('utf-8'))
        if sys.version_info.major > 2:
            try:
                return hash_func(bytes(obj))
            except TypeError:
                return None
        else:
            return None
