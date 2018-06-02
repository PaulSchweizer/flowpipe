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
import inspect
import json
import uuid

from .plug import OutputPlug, InputPlug
from .log_observer import LogObserver
__all__ = ['INode']


class INode(object):
    """Holds input and output Plugs and a method for computing."""

    __metaclass__ = ABCMeta

    def __init__(self, name=None, identifier=None, engine="tk-shell"):
        """Initialize the input and output dictionaries and the name.

        Args:
            name (str): If not provided, the class name is used.
        """
        self.name = name if name is not None else self.__class__.__name__
        self.identifier = (identifier if identifier is not None
                           else '{0}-{1}'.format(self.name, uuid.uuid4()))
        self.inputs = dict()
        self.outputs = dict()
        self.engine = engine
        self.omit = False
        self.file_location = inspect.getfile(self.__class__)
        self.class_name = self.__class__.__name__

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
        if self.omit:
            LogObserver.push_message('Omitting {0} -> {1}'.format(
                self.file_location, self.class_name))
            return {}

        inputs = {}
        for name, plug in self.inputs.items():
            inputs[name] = plug.value

        LogObserver.push_message('Evaluating {0} -> {1}.compute(**{2})'
            .format(self.file_location, self.class_name,
                    json.dumps(self._sort_plugs(inputs), indent=2)))

        inputs = {}
        for name, plug in self.inputs.items():
            inputs[name] = plug.value

        # Compute and redirect the output to the output plugs
        outputs = self.compute(**inputs) or dict()
        for name, value in outputs.items():
            self.outputs[name].value = value

        # Set the inputs clean
        for input_ in self.inputs.values():
            input_.is_dirty = False

        LogObserver.push_message('Evaluation result: {2}'
            .format(self.file_location, self.class_name,
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
            module=self.__module__,
            cls=self.__class__.__name__,
            name=self.name,
            identifier=self.identifier,
            inputs=inputs,
            outputs=outputs,
            engine=self.engine)

    @staticmethod
    def deserialize(data):
        """De-serialize from the given json data."""
        try:
            module = importlib.import_module(data['module'])
        except NameError:
            module = __import__(data['module'], globals(),
                                locals(), ['object'], -1)
        node = getattr(module, data['cls'], None)()
        node.post_deserialize(data)
        return node

    def post_deserialize(self, data):
        """Perform more data operations after initial serialization."""
        self.name = data['name']
        self.identifier = data['identifier']
        self.engine = data['engine']
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
        max_value_length = 0

        offset = ''
        if [i for i in self.inputs.values() if i.connections]:
            offset = ' ' * 3
        width = len(max(list(self.inputs) +
                        list(self.outputs) +
                        [self.name] +
                        list(plug.name + "".join([s for i, s in enumerate(str(plug.value)) if i < max_value_length]) for plug in self.inputs.values() if plug.value is not None) +
                        list(plug.name + "".join([s for i, s in enumerate(str(plug.value)) if i < max_value_length]) for plug in self.outputs.values() if plug.value is not None),
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
            plug = 'o {input_}<{value}>'.format(input_=input_, value="".join([s for i, s in enumerate(str(value)) if i < max_value_length]))
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

    def _sort_plugs(self, plugs):
        sorted_plugs = OrderedDict()
        for i in sorted(plugs, key=lambda x: x.lower()):
            sorted_plugs[i] = plugs[i]
        return sorted_plugs


class FunctionNode(INode):
    """Wrap a function into a Node."""

    def __init__(self, func=None, outputs=None, name=None,
                 identifier=None, engine='tk-shell', **kwargs):
        """The data on the function is used to drive the Node.
        The function itself becomes the compute method.
        The function input args become the InputPlugs.
        Other function attributes, name, __doc__ also transfer to the Node.
        """
        super(FunctionNode, self).__init__(
            name or getattr(func, '__name__', None), identifier, engine)
        self._initialize(func, outputs or [], engine)
        for plug, value in kwargs.items():
            self.inputs[plug].value = value

        if func is not None:
            self.file_location = inspect.getfile(func)
            self.class_name = self.func.__name__

    def __call__(self, **kwargs):
        """Create and return an instance of the Node."""
        return FunctionNode(func=self.func,
                            outputs=[o for o in self.outputs],
                            engine=self.engine,
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
        module = __import__(data['func']['module'], globals(), locals(), ['object'], -1)
        node = getattr(module, data['func']['name'], None)()
        self._initialize(node.func, data['outputs'].keys(), data['engine'])
        for name, input_ in data['inputs'].items():
            self.inputs[name].value = input_['value']

    def _initialize(self, func, outputs, engine):
        """Use the function and the list of outputs to setup the Node."""
        self.func = func
        self.__doc__ = func.__doc__
        self._use_self = False
        self.engine = engine
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
