"""Flow-based programming with python."""

import logging


PACKAGE = 'flowpipe'


# create logger
logger = logging.getLogger(PACKAGE)
logger.propagate = False

# create console handler and set level to debug
handler = logging.StreamHandler()

# create formatter
formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')

# add formatter to handler
handler.setFormatter(formatter)

# add handler to logger
logger.addHandler(handler)

from .graph import Graph
from .node import INode, Node
from .plug import InputPlug, OutputPlug, SubInputPlug, SubOutputPlug
