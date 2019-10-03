"""Nodes manipulate incoming data and provide the outgoing data."""
from __future__ import print_function
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import copy
import inspect
import json
import time
import uuid
import warnings

from .plug import OutputPlug, InputPlug, SubInputPlug, SubOutputPlug
from .log_observer import LogObserver
from .stats_reporter import StatsReporter
from .utilities import deserialize_node, NodeEncoder, import_class
from .graph import get_default_graph
__all__ = ['INode']


# Use getfullargspec on py3.x to make type hints work
try:
    getargspec = inspect.getfullargspec
except AttributeError:
    getargspec = inspect.getargspec


class INode(object):
    """Holds input and output Plugs and a method for computing."""

    __metaclass__ = ABCMeta

    def __init__(self, name=None, identifier=None, metadata=None,
                 graph='default'):
        """Initialize the input and output dictionaries and the name.

        Args:
            name (str): If not provided, the class name is used.
            graph (Graph): The graph to add the node to.
                If set to 'default', the Node is added to the default graph.
                If set to None, the Node is not added to any grpah.

        """
        self.name = name if name is not None else self.__class__.__name__
        self.identifier = (identifier if identifier is not None
                           else '{0}-{1}'.format(self.name, uuid.uuid4()))
        self.inputs = dict()
        self.outputs = dict()
        self.metadata = metadata or {}
        self.omit = False
        try:
            self.file_location = inspect.getfile(self.__class__)
        except TypeError as e:  # pragma: no cover
            # Excluded from tests, as this is a hard-to test fringe case
            if str(e) == "<module '__main__'> is a built-in class":
                warnings.warn("Cannot serialize nodes defined in '__main__'")
                self.file_location = None
            else:
                raise
        self.class_name = self.__class__.__name__
        if graph is not None:
            if graph == 'default':
                get_default_graph().add_node(self)
            else:
                graph.add_node(self)

    def __unicode__(self):
        """Show all input and output Plugs."""
        return self.node_repr()

    def __str__(self):
        """Show all input and output Plugs."""
        return self.__unicode__().encode('utf-8').decode()

    @property
    def is_dirty(self):
        """Whether any of the input Plug data has changed and is dirty."""
        for input_ in self.inputs.values():
            if input_.is_dirty:
                return True
        return False

    @property
    def upstream_nodes(self):
        """Upper level Nodes feed inputs into this Node."""
        upstream_nodes = list()
        for input_ in self.inputs.values():
            upstream_nodes += [c.node for c in input_.connections]
            for sub_plug in input_._sub_plugs.values():
                upstream_nodes += [c.node for c in sub_plug.connections]
        return list(set(upstream_nodes))

    @property
    def downstream_nodes(self):
        """Lower level nodes that this node feeds output to."""
        downstream_nodes = list()
        for output in self.outputs.values():
            downstream_nodes += [c.node for c in output.connections]
            for sub_plug in output._sub_plugs.values():
                downstream_nodes += [c.node for c in sub_plug.connections]
        return list(set(downstream_nodes))

    def evaluate(self):
        """Compute this Node, log it and clean the input Plugs.

        Also push a stat report in the following form containing the Node,
        evaluation time and timestamp the computation started.
        """
        if self.omit:
            LogObserver.push_message('Omitting {0} -> {1}'.format(
                self.file_location, self.class_name))
            return {}

        inputs = {}
        for name, plug in self.inputs.items():
            inputs[name] = plug.value

        LogObserver.push_message(
            'Evaluating {0} -> {1}.compute(**{2})'.format(
                self.file_location, self.class_name,
                json.dumps(self._sort_plugs(inputs), indent=2, cls=NodeEncoder)
            ))

        # Compute and redirect the output to the output plugs
        start_time = time.time()
        outputs = self.compute(**inputs) or dict()
        eval_time = time.time() - start_time

        stats = {
            "node": self,
            "eval_time": eval_time,
            "timestamp": start_time
        }

        StatsReporter.push_stats(stats)

        # all_outputs = self.all_outputs()
        for name, value in outputs.items():
            if '.' in name:
                parent_plug, sub_plug = name.split('.')
                self.outputs[parent_plug][sub_plug].value = value
            else:
                self.outputs[name].value = value

        # Set the inputs clean
        for input_ in self.all_inputs().values():
            input_.is_dirty = False

        LogObserver.push_message(
            'Evaluation result for {0} -> {1}: {2}'.format(
                self.file_location, self.class_name,
                json.dumps(self._sort_plugs(outputs), indent=2, cls=NodeEncoder)
            ))

        return outputs

    @abstractmethod
    def compute(self, *args, **kwargs):
        """Implement the data manipulation in the subclass.

        Return a dictionary with the outputs from this function.
        """

    def on_input_plug_set_dirty(self):
        """Propagate the dirty state to the connected downstream nodes."""
        for output_plug in self.outputs.values():
            for connected_plug in output_plug.connections:
                connected_plug.is_dirty = True

    def serialize(self):
        """Serialize the node to json."""
        if self.file_location is None:  # pragma: no cover
            raise RuntimeError("Cannot serialize a node that was not defined "
                               "in a file")
        inputs = OrderedDict()
        for plug in self.inputs.values():
            inputs[plug.name] = plug.serialize()
        outputs = OrderedDict()
        for plug in self.outputs.values():
            outputs[plug.name] = plug.serialize()
        return OrderedDict(
            file_location=self.file_location,
            module=self.__module__,
            cls=self.__class__.__name__,
            name=self.name,
            identifier=self.identifier,
            inputs=inputs,
            outputs=outputs,
            metadata=self.metadata)

    @staticmethod
    def deserialize(data):
        """De-serialize from the given json data."""
        return deserialize_node(data)

    def post_deserialize(self, data):
        """Perform more data operations after initial serialization."""
        self.name = data['name']
        self.identifier = data['identifier']
        self.metadata = data['metadata']
        self.file_location = data['file_location']
        for name, input_ in data['inputs'].items():
            self.inputs[name].value = input_['value']
            for sub_name, sub_plug in input_['sub_plugs'].items():
                self.inputs[name][sub_name].value = sub_plug['value']
        for name, output in data['outputs'].items():
            self.outputs[name].value = output['value']
            for sub_name, sub_plug in output['sub_plugs'].items():
                self.outputs[name][sub_name].value = sub_plug['value']

    def node_repr(self):
        """The node formated into a string looking like a node.

        +------------------+
        |     Node.Name    |
        |------------------|
        % compound_in      |
        o  compound_in-1   |
        o  compound_in-2   |
        o in               |
        |              out o
        |     compound_out %
        |  compound_out-1  o
        |  compound_out-2  o
        +------------------+
        """
        max_value_length = 10

        all_inputs = self.all_inputs()
        all_outputs = self.all_outputs()

        offset = ''
        if [i for i in all_inputs.values() if i.connections]:
            offset = ' ' * 3

        width = len(max(list(all_inputs) +
                        list(all_outputs) +
                        [self.name] +
                        list(plug.name + "".join([
                            s for i, s in enumerate(str(plug.value))
                            if i < max_value_length])
                            for plug in all_inputs.values()
                            if plug.value is not None) +
                        list(plug.name + "".join([
                            s for i, s in enumerate(str(plug.value))
                            if i < max_value_length])
                            for plug in all_outputs.values()
                            if plug.value is not None),
                        key=len)) + 7

        pretty = offset + '+' + '-' * width + '+'
        pretty += '\n{offset}|{name:^{width}}|'.format(
            offset=offset, name=' ' + self.name + ' ', width=width)
        pretty += '\n' + offset + '|' + '-' * width + '|'

        # Inputs
        for input_ in sorted(all_inputs.keys()):
            pretty += '\n'
            in_plug = all_inputs[input_]
            if in_plug.connections:
                pretty += '-->'
            else:
                pretty += offset

            value = ""
            if in_plug.value is not None:
                value = json.dumps(in_plug.value, cls=NodeEncoder)
            plug = '{symbol} {dist}{input_}{value}'.format(
                symbol='%' if in_plug._sub_plugs else 'o',
                dist=' ' if isinstance(in_plug, SubInputPlug)else '',
                input_=input_,
                value=('<{value}>'.format(value=''.join(
                    [s for i, s in enumerate(str(value))
                     if i < max_value_length]))
                    if not in_plug._sub_plugs else ''))
            pretty += '{plug:{width}}|'.format(plug=plug, width=width + 1)

        # Outputs
        all_outputs = self.all_outputs()
        for output in sorted(all_outputs.keys()):
            out_plug = all_outputs[output]
            dist = 2 if isinstance(out_plug, SubOutputPlug) else 1
            pretty += '\n{offset}|{output:>{width}}{dist}{symbol}'.format(
                offset=offset, output=output, width=width - dist,
                dist=dist * ' ',
                symbol='%' if out_plug._sub_plugs else 'o')
            if all_outputs[output].connections:
                pretty += '---'

        pretty += '\n' + offset + '+' + '-' * width + '+'
        return pretty

    def list_repr(self):
        """List representation of the node showing inputs and their values.

        Node
          [i] in: "A"
          [i] in_compound
           [i] in_compound.0: "B"
           [i] in_compound.1 << Node1.out
          [o] compound_out
           [o] in_compound.0: null
           [o] compound_out.1 >> Node2.in, Node3.in
          [o] out >> Node4.in
        """
        pretty = []
        pretty.append(self.name)
        for name, plug in sorted(self.all_inputs().items()):
            if plug._sub_plugs:
                pretty.append('  [i] {name}'.format(name=name))
                continue
            if plug.connections:
                pretty.append('{indent}[i] {name} << {node}.{plug}'.format(
                    indent='   ' if isinstance(plug, SubInputPlug) else '  ',
                    name=name,
                    node=plug.connections[0].node.name,
                    plug=plug.connections[0].name))
            else:
                pretty.append('{indent}[i] {name}: {value}'.format(
                    indent='   ' if isinstance(plug, SubInputPlug) else '  ',
                    name=name,
                    value=json.dumps(plug.value, cls=NodeEncoder)))
        for name, plug in sorted(self.all_outputs().items()):
            if plug._sub_plugs:
                pretty.append('  [o] {name}'.format(name=name))
                continue
            if plug.connections:
                pretty.append('{indent}[o] {name} >> {connections}'.format(
                    indent='   ' if isinstance(plug, SubOutputPlug) else '  ',
                    name=name,
                    connections=', '.join(
                        ['{node}.{plug}'.format(node=c.node.name, plug=c.name)
                         for c in plug.connections])))
            else:
                pretty.append('{indent}[o] {name}: {value}'.format(
                    indent='   ' if isinstance(plug, SubOutputPlug) else '  ',
                    name=name,
                    value=json.dumps(plug.value, cls=NodeEncoder)))

        return '\n'.join(pretty)

    def all_inputs(self):
        """Collate all input plugs and their sub_plugs into one dictionary."""
        all_inputs = {}
        for plug in self.inputs.values():
            all_inputs[plug.name] = plug
            for sub in plug._sub_plugs.values():
                all_inputs[sub.name] = sub
        return all_inputs

    def all_outputs(self):
        """Collate all output plugs and their sub_plugs into one dictionary."""
        all_outputs = {}
        for plug in self.outputs.values():
            all_outputs[plug.name] = plug
            for sub in plug._sub_plugs.values():
                all_outputs[sub.name] = sub
        return all_outputs

    @staticmethod
    def _sort_plugs(plugs):
        """Sort the given plugs alphabetically into an OrderedDict."""
        sorted_plugs = OrderedDict()
        for i in sorted(plugs, key=lambda x: x.lower()):
            sorted_plugs[i] = plugs[i]
        return sorted_plugs


class FunctionNode(INode):
    """Wrap a function into a Node."""

    # Some names have to stay reserved as they are used to construct the Node
    RESERVED_INPUT_NAMES = (
        "func", "name", "identifier", "inputs", "outputs", "metadata", "omit",
        "graph")

    def __init__(self, func=None, outputs=None, name=None,
                 identifier=None, metadata=None, graph=None, **kwargs):
        """The data on the function is used to drive the Node.
        The function itself becomes the compute method.
        The function input args become the InputPlugs.
        Other function attributes, name, __doc__ also transfer to the Node.
        """
        super(FunctionNode, self).__init__(
            name or getattr(func, '__name__', None),
            identifier, metadata, graph)
        self._initialize(func, outputs or [], metadata)
        for plug, value in kwargs.items():
            self.inputs[plug].value = value

    def __call__(self, **kwargs):
        """Create and return an instance of the Node."""
        metadata = copy.deepcopy(self.metadata)
        metadata.update(kwargs.pop("metadata", {}))
        graph = kwargs.pop('graph', 'default')
        return self.__class__(func=self.func,
                              outputs=[o for o in self.outputs],
                              metadata=metadata,
                              graph=graph,
                              **kwargs)

    def compute(self, *args, **kwargs):
        """Call and return the wrapped function."""
        if self._use_self:
            return self.func(self, *args, **kwargs)
        else:
            return self.func(*args, **kwargs)

    def serialize(self):
        """Also serialize the location of the wrapped function."""
        data = super(FunctionNode, self).serialize()
        data['func'] = {
            'module': self.func.__module__,
            'name': self.func.__name__
        }
        return data

    def post_deserialize(self, data):
        """Apply the function back to the node."""
        self.name = data['name']
        self.identifier = data['identifier']
        self.metadata = data['metadata']
        self.file_location = data['file_location']
        node = import_class(
            data['func']['module'],
            data['func']['name'],
            data['file_location'])(graph=None)
        self._initialize(node.func, data['outputs'].keys(), data['metadata'])
        for name, input_ in data['inputs'].items():
            self.inputs[name].value = input_['value']
            for sub_name, sub_plug in input_['sub_plugs'].items():
                self.inputs[name][sub_name].value = sub_plug['value']
        for name, output in data['outputs'].items():
            self.outputs[name].value = output['value']
            for sub_name, sub_plug in output['sub_plugs'].items():
                self.outputs[name][sub_name].value = sub_plug['value']

    def _initialize(self, func, outputs, metadata):
        """Use the function and the list of outputs to setup the Node."""
        self.func = func
        self.__doc__ = func.__doc__
        self._use_self = False
        self.metadata = metadata or {}
        if func is not None:
            self.file_location = inspect.getfile(func)
            self.class_name = self.func.__name__
            arg_spec = getargspec(func)
            defaults = {}
            if arg_spec.defaults is not None:
                defaults = dict(zip(arg_spec.args[-len(arg_spec.defaults):],
                                    arg_spec.defaults))
            forbidden_inputs = []
            for input_ in arg_spec.args:
                if input_ in self.RESERVED_INPUT_NAMES:
                    forbidden_inputs.append(input_)
                    continue
                if input_ != 'self':
                    plug = InputPlug(input_, self)
                    plug.value = defaults.get(input_, None)
                else:
                    self._use_self = True
            if forbidden_inputs:
                raise ValueError(
                    "{0} are reserved names and can not be used as inputs!\n"
                    "Reserved names are: {1}".format(
                        ", ".join(forbidden_inputs),
                        self.RESERVED_INPUT_NAMES))

        if outputs is not None:
            for output in outputs:
                OutputPlug(output, self)


def Node(*args, **kwargs):
    """Wrap the given function into a Node."""
    cls = kwargs.pop("cls", FunctionNode)

    def node(func):
        return cls(func, *args, **kwargs)
    return node
