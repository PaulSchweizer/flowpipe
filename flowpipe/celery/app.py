"""The Celery app."""
from __future__ import absolute_import, unicode_literals
import json
import importlib

from celery import Celery


app = Celery('flowpipe', broker='pyamqp://')
app.conf.update(CELERY_RESULT_BACKEND='redis://',
                CELERY_TASK_SERIALIZER='json',
                CELERY_RESULT_SERIALIZER='json')


@app.task(bind=True)
def evaluate_node(self, node_dump, *args, **kwargs):
    """Grab inputs from disc, evaluate node and dump result to disc."""
    # Reconstruct the Node
    #
    mod = importlib.import_module(node_dump['module'])
    node = getattr(mod, node_dump['cls'])()
    node.deserialize(node_dump)

    # 1. Get input values from connected upstream nodes from Redis
    #
    for name, data in node_dump['inputs'].items():
        node.inputs[name].value = data['value']
        for connection_node, plug in data['connections'].items():
            connected_data = json.loads(self.backend.get(connection_node))
            node.inputs[name].value = connected_data['outputs'][plug]['value']

    # 2.Evaluate
    #
    node.evaluate()

    data = node.serialize()

    # 3. Store under node.identifier in the redis backend
    #
    self.backend.set(node.identifier, json.dumps(data, indent=2))

    return data


if __name__ == '__main__':
    app.start()
