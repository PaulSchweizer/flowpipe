try:
    import importlib
except ImportError:
    pass
import imp


def import_class(module, cls_name, file_location=None):
    """Import and return the given class from the given module.

    File location can be given to import the class from a location that
    is not accessible through the PYTHONPATH.
    This works from python 2.6 to python 3.
    """
    try:
        module = importlib.import_module(module)
    except NameError:
        module = __import__(module, globals(), locals(), ['object'], -1)
    try:
        cls = getattr(module, cls_name)
    except AttributeError:
        module = imp.load_source('module', file_location)
        cls = getattr(module, cls_name)
    return cls
