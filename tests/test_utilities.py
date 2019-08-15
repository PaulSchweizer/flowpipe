from __future__ import print_function

import pytest

import json
from hashlib import sha256

import flowpipe.utilities as util


def test_node_encoder():
    """Test the custom JSONEncoder."""
    valid_object = {"key": "value", "other_key": [1, 2, 3]}
    expected_json = '{"key": "value", "other_key": [1, 2, 3]}'
    json_string = json.dumps(valid_object)
    assert json_string == expected_json

    invalid_object = {"key": "value", "other_key": bytes(42)}
    with pytest.raises(TypeError):
        json.dumps(invalid_object)
    json_string = json.dumps(invalid_object, cls=util.NodeEncoder)
    expected_json = '{"key": "value", "other_key": "094c4931fdb2f2af417c9e0322a9716006e8211fe9017f671ac6e3251300acca"}'
    assert json_string == expected_json
