from __future__ import print_function

import pytest

import json
import re
from hashlib import sha256

import numpy as np

import flowpipe.utilities as util


class WeirdObject(object):
    """An object that is not json serializable and has no bytes() interface."""

    foo = "bar"


def test_node_encoder():
    """Test the custom JSONEncoder."""
    valid_object = {"key": "value", "other_key": [1, 2, 3]}
    json_string = json.dumps(valid_object)
    recovered_json = json.loads(json_string)
    for k, v in valid_object.items():
        assert v == recovered_json[k]

    bytes_object = {"key": "value", "other_key": bytes(42)}
    json_string = json.dumps(bytes_object, cls=util.NodeEncoder)
    recovered_json = json.loads(json_string)
    for k, v in bytes_object.items():
        assert v == recovered_json[k] \
            or sha256(v).hexdigest() == recovered_json[k]

    weird_object = {"key": "value", "other_key": WeirdObject()}
    json_string = json.dumps(weird_object, cls=util.NodeEncoder)
    recovered_json = json.loads(json_string)
    for k, v in weird_object.items():
        assert v == recovered_json[k] \
            or re.search('WeirdObject object at', str(recovered_json[k])) \
            or sha256(v).hexdigest() == recovered_json[k]

    weird_np_array = {"key": "value", "other_key": np.arange(10)[::2]}
    json_string = json.dumps(weird_np_array, cls=util.NodeEncoder)
    recovered_json = json.loads(json_string)
    for k, v in weird_np_array.items():
        assert v == recovered_json[k]\
            or sha256(bytes(v)).hexdigest() == recovered_json[k]
