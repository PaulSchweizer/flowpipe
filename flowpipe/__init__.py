"""Flow-based programming with python."""
import logging


PACKAGE = 'flowpipe'

# create logger
logger = logging.getLogger(PACKAGE)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')

# add formatter to handler
handler.setFormatter(formatter)

# add handler to logger
logger.addHandler(handler)
