from __future__ import print_function

import pytest

import json
from hashlib import sha256

import flowpipe.utilities as util


def test_node_encoder():
    """Test the custom JSONEncoder."""
    valid_object = {"key": "value", "other_key": [1, 2, 3]}
    json_string = json.dumps(valid_object)
    recovered_json = json.loads(json_string)
    for k, v in valid_object.items():
        assert v == recovered_json[k]

    invalid_object = {"key": "value", "other_key": bytes(42)}
    json_string = json.dumps(invalid_object, cls=util.NodeEncoder)
    recovered_json = json.loads(json_string)
    for k, v in invalid_object.items():
        assert v == recovered_json[k] or sha256(v).hexdigest() == recovered_json[k]
