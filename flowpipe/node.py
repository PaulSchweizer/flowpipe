"""Nodes manipulate incoming data and provide the outgoing data."""
from __future__ import print_function
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
try:
    import importlib
except ImportError:
    pass
import copy
import imp
import inspect
import json
import time
import uuid

from .plug import OutputPlug, InputPlug
from .log_observer import LogObserver
from .stats_reporter import StatsReporter
from .utilities import import_class
__all__ = ['INode']


class INode(object):
    """Holds input and output Plugs and a method for computing."""

    __metaclass__ = ABCMeta

    def __init__(self, name=None, identifier=None, metadata=None, graph=None):
        """Initialize the input and output dictionaries and the name.

        Args:
            name (str): If not provided, the class name is used.
        """
        self.name = name if name is not None else self.__class__.__name__
        self.identifier = (identifier if identifier is not None
                           else '{0}-{1}'.format(self.name, uuid.uuid4()))
        self.inputs = dict()
        self.outputs = dict()
        self.metadata = metadata or {}
        self.omit = False
        self.file_location = inspect.getfile(self.__class__)
        self.class_name = self.__class__.__name__
        if graph is not None:
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
        return list(set(upstream_nodes))

    @property
    def downstream_nodes(self):
        """Lower level nodes that this node feeds output to."""
        downstream_nodes = list()
        for output in self.outputs.values():
            downstream_nodes += [c.node for c in output.connections]
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
                json.dumps(self._sort_plugs(inputs), indent=2)))

        inputs = {}
        for name, plug in self.inputs.items():
            inputs[name] = plug.value

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

        for name, value in outputs.items():
            self.outputs[name].value = value

        # Set the inputs clean
        for input_ in self.inputs.values():
            input_.is_dirty = False

        LogObserver.push_message(
            'Evaluation result for {0} -> {1}: {2}'.format(
                self.file_location, self.class_name,
                json.dumps(self._sort_plugs(outputs), indent=2)))

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
        node = import_class(
            data['module'], data['cls'], data['file_location'])()
        node.post_deserialize(data)
        return node

    def post_deserialize(self, data):
        """Perform more data operations after initial serialization."""
        self.name = data['name']
        self.identifier = data['identifier']
        self.metadata = data['metadata']
        self.file_location = data['file_location']
        for name, input_ in data['inputs'].items():
            self.inputs[name].value = input_['value']

    def node_repr(self):
        """The node formated into a string looking like a node.

        +------------+
        | Node.Name  |
        |------------|
        o in         |
        |        out o
        +------------+
        """
        max_value_length = 10

        offset = ''
        if [i for i in self.inputs.values() if i.connections]:
            offset = ' ' * 3
        width = len(max(list(self.inputs) +
                        list(self.outputs) +
                        [self.name] +
                        list(plug.name + "".join([
                            s for i, s in enumerate(str(plug.value))
                            if i < max_value_length])
                            for plug in self.inputs.values()
                            if plug.value is not None) +
                        list(plug.name + "".join([
                            s for i, s in enumerate(str(plug.value))
                            if i < max_value_length])
                            for plug in self.outputs.values()
                            if plug.value is not None),
                        key=len)) + 5
        pretty = offset + '+' + '-' * width + '+'
        pretty += '\n{offset}|{name:^{width}}|'.format(
            offset=offset, name=' ' + self.name + ' ', width=width)
        pretty += '\n' + offset + '|' + '-' * width + '|'
        # Inputs
        for input_ in sorted(self.inputs.keys()):
            pretty += '\n'
            if self.inputs[input_].connections:
                pretty += '-->'
            else:
                pretty += offset

            value = ""
            if self.inputs[input_].value is not None:
                value = json.dumps(self.inputs[input_].value)
            plug = 'o {input_}<{value}>'.format(
                input_=input_,
                value="".join([s for i, s in enumerate(str(value))
                               if i < max_value_length]))
            pretty += '{plug:{width}}|'.format(plug=plug, width=width + 1)

        # Outputs
        for output in sorted(self.outputs.keys()):
            pretty += '\n{offset}|{output:>{width}} o'.format(
                offset=offset, output=output, width=width - 1)
            if self.outputs[output].connections:
                pretty += '---'

        pretty += '\n' + offset + '+' + '-' * width + '+'
        return pretty

    def list_repr(self):
        """List representation of the node showing inputs and their values."""
        pretty = []
        pretty.append(self.name)
        for name, plug in self.inputs.items():
            if plug.connections:
                pretty.append('  [i] {0} << {1}.{2}'.format(
                    name, plug.connections[0].node.name,
                    plug.connections[0].name))
            else:
                pretty.append('  [i] {0}: {1}'.format(name,
                                                      json.dumps(plug.value)))
        for name, plug in self.outputs.items():
            if plug.connections:
                pretty.append('  [o] {0} >> {1}.{2}'.format(
                    name, plug.connections[0].node.name,
                    plug.connections[0].name))
            else:
                pretty.append('  [o] {0}'.format(name))
        return '\n'.join(pretty)

    @staticmethod
    def _sort_plugs(plugs):
        sorted_plugs = OrderedDict()
        for i in sorted(plugs, key=lambda x: x.lower()):
            sorted_plugs[i] = plugs[i]
        return sorted_plugs


class FunctionNode(INode):
    """Wrap a function into a Node."""

    def __init__(self, func=None, outputs=None, name=None,
                 identifier=None, metadata=None, graph=None, **kwargs):
        """The data on the function is used to drive the Node.
        The function itself becomes the compute method.
        The function input args become the InputPlugs.
        Other function attributes, name, __doc__ also transfer to the Node.
        """
        super(FunctionNode, self).__init__(
            name or getattr(func, '__name__', None), identifier, metadata, graph)
        self._initialize(func, outputs or [], metadata)
        for plug, value in kwargs.items():
            self.inputs[plug].value = value

    def __call__(self, **kwargs):
        """Create and return an instance of the Node."""
        metadata = copy.deepcopy(self.metadata)
        metadata.update(kwargs.pop("metadata", {}))
        return self.__class__(func=self.func,
                              outputs=[o for o in self.outputs],
                              metadata=metadata,
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
        module = imp.load_source('module', data['file_location'])
        node = getattr(module, data['func']['name'])()
        self._initialize(node.func, data['outputs'].keys(), data['metadata'])
        for name, input_ in data['inputs'].items():
            self.inputs[name].value = input_['value']

    def _initialize(self, func, outputs, metadata):
        """Use the function and the list of outputs to setup the Node."""
        self.func = func
        self.__doc__ = func.__doc__
        self._use_self = False
        self.metadata = metadata or {}
        if func is not None:
            self.file_location = inspect.getfile(func)
            self.class_name = self.func.__name__
            arg_spec = inspect.getargspec(func)
            defaults = {}
            if arg_spec.defaults is not None:
                defaults = dict(zip(arg_spec.args[-len(arg_spec.defaults):],
                                    arg_spec.defaults))
            for input_ in arg_spec.args:
                if input_ != 'self':
                    plug = InputPlug(input_, self)
                    plug.value = defaults.get(input_, None)
                else:
                    self._use_self = True
        if outputs is not None:
            for output in outputs:
                OutputPlug(output, self)


def Node(*args, **kwargs):
    """Wrap the given function into a Node."""
    cls = kwargs.pop("cls", FunctionNode)

    def node(func):
        return cls(func, *args, **kwargs)
    return node
