from __future__ import print_function

import json
import re
import sys
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
        assert (
            v == recovered_json[k]
            or sha256(v).hexdigest() == recovered_json[k]
        )

    weird_object = {"key": "value", "other_key": WeirdObject()}
    json_string = json.dumps(weird_object, cls=util.NodeEncoder)
    recovered_json = json.loads(json_string)
    for k, v in weird_object.items():
        assert (
            v == recovered_json[k]
            or re.search("WeirdObject object at", str(recovered_json[k]))
            or sha256(v).hexdigest() == recovered_json[k]
        )

    weird_np_array = {"key": "value", "other_key": np.arange(10)[::2]}
    json_string = json.dumps(weird_np_array, cls=util.NodeEncoder)
    recovered_json = json.loads(json_string)
    for k, v in weird_np_array.items():
        assert (
            # v could be any type, so for simplicity we cast to str
            str(v) == str(recovered_json[k])
            or sha256(bytes(v)).hexdigest() == recovered_json[k]
        )


def test_get_hash():
    """Test the hashing function."""
    number = 42
    assert (
        util.get_hash(number)
        == "73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049"
    )

    js = {"foo": "bar", "baz": {"zoom": "zulu"}}
    assert (
        util.get_hash(js)
        == "8336ea0f6e482df0c7a738c83a2b8d3357cf0234c29cfd232fa6627bdc54289e"
    )

    invalid_js = "kazoo{"  # A generic string that's not json
    if sys.version_info.major > 2:
        assert (
            util.get_hash(invalid_js)
            == "c21e3435e752b72514e34139f116afee1f72cf496c1cc94c9087088c139dfb7d"
        )
    else:
        assert (
            util.get_hash(invalid_js)
            == "5324bcf2641f119108d1f99b92687b0af513e572c68dfed217344ffeff1f35a9"
        )

    x = WeirdObject()
    assert util.get_hash(x) is None
