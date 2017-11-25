"""Nodes manipulate incoming data and provide the outgoing data."""
from __future__ import print_function
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import importlib
import inspect
import json
import uuid

from .plug import OutputPlug, InputPlug
from .log_observer import LogObserver
__all__ = ['INode']


class INode(object):
    """Holds input and output Plugs and a method for computing."""

    __metaclass__ = ABCMeta

    def __init__(self, name=None, identifier=None):
        """Initialize the input and output dictionaries and the name.

        Args:
            name (str): If not provided, the class name is used.
        """
        self.name = name if name is not None else self.__class__.__name__
        self.identifier = (identifier if identifier is not None
                           else '{0}-{1}'.format(self.name, uuid.uuid4()))
        self.inputs = dict()
        self.outputs = dict()

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
        """Compute this Node, log it and clean the input Plugs."""
        inputs = {name: plug.value for name, plug in self.inputs.items()}

        # Compute and redirect the output to the output plugs
        outputs = self.compute(**inputs) or dict()
        for name, value in outputs.items():
            self.outputs[name].value = value

        # Set the inputs clean
        for input_ in self.inputs.values():
            input_.is_dirty = False

        LogObserver.push_message('Computed: {}'.format(self.name))

        return outputs

    @abstractmethod
    def compute(self, *args, **kwargs):
        """Implement the data manipulation in the subclass.

        Return a dictionary with the outputs from this function.
        """
        pass

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
            module=self.__module__,
            cls=self.__class__.__name__,
            name=self.name,
            identifier=self.identifier,
            inputs=inputs,
            outputs=outputs)

    @staticmethod
    def deserialize(data):
        """De-serialize from the given json data."""
        cls = getattr(importlib.import_module(data['module']),
                      data['cls'], None)
        node = cls()
        node.post_deserialize(data)
        return node

    def post_deserialize(self, data):
        """Perform more data operations after initial serialization."""
        self.name = data['name']
        self.identifier = data['identifier']
        for name, input_ in data['inputs'].items():
            self.inputs[name].value = input_['value']

    def node_repr(self):
        """Format the Node into a string looking like a node.

        +------------+
        | Node.Name  |
        |------------|
        o in         |
        |        out o
        +------------+
        """
        offset = ''
        if [i for i in self.inputs.values() if i.connections]:
            offset = ' ' * 3
        width = len(max(list(self.inputs) + list(self.outputs) +
                        [self.name], key=len)) + 2
        pretty = offset + '+' + '-' * width + '+'
        pretty += '\n{offset}|{name:^{width}}|'.format(
            offset=offset, name=' ' + self.name + ' ', width=width)
        pretty += '\n' + offset + '|' + '-' * width + '|'
        # Inputs
        for input_ in self.inputs.keys():
            pretty += '\n'
            if self.inputs[input_].connections:
                pretty += '-->'
            else:
                pretty += offset
            pretty += 'o {input_:{width}}|'.format(
                input_=input_, width=width - 1)

        # Outputs
        for output in self.outputs.keys():
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


class FunctionNode(INode):
    """Wrap a function into a Node."""

    def __init__(self, func=None, outputs=None, **kwargs):
        """The data on the function is used to drive the Node.
        The function itself becomes the compute method.
        The function input args become the InputPlugs.
        Other function attributes, name, __doc__ also transfer to the Node.
        """
        super(FunctionNode, self).__init__(
            name=getattr(func, '__name__', None))
        self._initialize(func, outputs or [])
        for plug, value in kwargs.items():
            self.inputs[plug].value = value

    def __call__(self, **kwargs):
        """Create and return an instance of the Node."""
        return self.__class__(func=self.func,
                              outputs=[o for o in self.outputs],
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
        node = getattr(importlib.import_module(
            data['func']['module']),
            data['func']['name'], None)()
        self._initialize(node.func, data['outputs'].keys())
        for name, input_ in data['inputs'].items():
            self.inputs[name].value = input_['value']

    def _initialize(self, func, outputs):
        """Use the function and the list of outputs to setup the Node."""
        self.func = func
        self.__doc__ = func.__doc__
        self._use_self = False
        if func is not None:
            for input_ in inspect.getargspec(func).args:
                if input_ != 'self':
                    InputPlug(input_, self)
                else:
                    self._use_self = True
        if outputs is not None:
            for output in outputs:
                OutputPlug(output, self)


def function_to_node(*args, **kwargs):
    """Wrap the given function into a Node."""
    def node(func):
        return FunctionNode(func, *args, **kwargs)
    return node
