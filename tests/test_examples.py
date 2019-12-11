import glob
import imp
import os


def test_examples():
    """Run the example files to ensure their integrity."""
    examples = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples', '*.py')

    for example in glob.glob(examples):
        imp.load_source(os.path.basename(example).replace('.', '_'), example)
