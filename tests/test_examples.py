import glob
import importlib.machinery
import importlib.util
import os
import sys


def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(
        modname, filename, loader=loader
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module


def test_examples():
    """Run the example files to ensure their integrity."""
    examples = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "examples", "*.py"
    )

    for example in glob.glob(examples):
        load_source(os.path.basename(example).replace(".", "_"), example)
