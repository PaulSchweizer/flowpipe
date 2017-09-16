"""Convert flowpipe graphs to Celery networks."""
from celery import chain, group, chord
from celery import signature

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph
from flowpipe.celery.app import evaluate_node, TestNode

# chain(evaluate_node.si(n1), evaluate_node.si(n2))()


def flowpipe_to_celery(graph):
    """Every row in the graph's evaluation grid converts to a group.

    The groups get chained.
    """
    # return chain([evaluate_node.si(n.serialize()) for n in graph.evaluation_sequence])

    groups = ([group([evaluate_node.si(n.serialize()) for n in row])
                  for row in graph.evaluation_grid])

    s = groups[0]
    for g in groups[1:]:
        s = s | g

    return s

    return chain([group([evaluate_node.si(n.serialize()) for n in row])
                  for row in graph.evaluation_grid])

# chain(evaluate_node.si(n1), evaluate_node.si(n2))()


if  __name__ == '__main__':
    v11 = TestNode('v11')
    v12 = TestNode('v12')
    r1 = TestNode('r1')

    v21 = TestNode('v21')
    r2 = TestNode('r2')

    v31 = TestNode('v31')
    v32 = TestNode('v32')
    r3 = TestNode('r3')

    result = TestNode('result')
    r4 = TestNode('r4')

    v11.outputs['out'] >> r1.inputs['in1']
    v12.outputs['out'] >> r1.inputs['in2']

    v21.outputs['out'] >> r2.inputs['in1']
    r1.outputs['out'] >> r2.inputs['in2']

    # r1.outputs['out'] >> r4.inputs['in2']

    v31.outputs['out'] >> r3.inputs['in1']
    v32.outputs['out'] >> r3.inputs['in2']

    r2.outputs['out'] >> result.inputs['in1']
    r3.outputs['out'] >> result.inputs['in2']

    graph = Graph(nodes=[v11, v12, v21, v31, v32,
                         r1, r3,
                         r2,
                         result])

    # Calculate an initial value
    v11.inputs['in1'].value = 1
    v11.inputs['in2'].value = 2

    v12.inputs['in1'].value = 1
    v12.inputs['in2'].value = 3

    v21.inputs['in1'].value = 1
    v21.inputs['in2'].value = 4

    v31.inputs['in1'].value = 1
    v31.inputs['in2'].value = 5

    v32.inputs['in1'].value = 1
    v32.inputs['in2'].value = 6



    g1 = group(evaluate_node.si(v11.serialize()),
               evaluate_node.si(v12.serialize()),
               evaluate_node.si(v21.serialize()),
               evaluate_node.si(v31.serialize()),
               evaluate_node.si(v32.serialize()))

    g2 = group(evaluate_node.si(r1.serialize()),
               evaluate_node.si(r3.serialize()))

    g3 = group(evaluate_node.si(r2.serialize()))

    g4 = group(evaluate_node.si(result.serialize()))

    # (g1 | g2 | g3 | g4)()

    # g1 = group(signature(evaluate_node, args=(v11.serialize())),
    #            signature(evaluate_node, args=(v12.serialize())),
    #            signature(evaluate_node, args=(v21.serialize())),
    #            signature(evaluate_node, args=(v31.serialize())),
    #            signature(evaluate_node, args=(v32.serialize())))
    # g2 = group(signature(evaluate_node, args=(r1.serialize())),
    #            signature(evaluate_node, args=(r3.serialize())))
    # g3 = group(signature(evaluate_node, args=(r2.serialize())))
    # g4 = group(signature(evaluate_node, args=(result.serialize())))

    # (g1 | g2 | g3 | g4)()


    g1 = group(evaluate_node.si(v11.serialize()),
               evaluate_node.si(v12.serialize()),
               evaluate_node.si(v21.serialize()),
               evaluate_node.si(v31.serialize()),
               evaluate_node.si(v32.serialize()))
    g2 = group(evaluate_node.si(r1.serialize()),
               evaluate_node.si(r3.serialize()))
    g3 = group(evaluate_node.si(r2.serialize()))
    g4 = group(evaluate_node.si(result.serialize()))

    ((g1 | g2 | g3) | g4)()

    res = flowpipe_to_celery(graph)
    # res()
    # print(res)

    # res = chain(add.s(4, 4), mul.s(8), mul.s(10))()


    # >>> callback = tsum.s()
    # >>> header = [add.s(i, i) for i in range(100)]
    # >>> result = chord(header)(callback)
    # >>> result.get()


    # Layer 4
    # result = evaluate_node.si(result.serialize())
    # v11 = evaluate_node.si(v11.serialize())
    # v12 = evaluate_node.si(v12.serialize())
    # r1 = evaluate_node.si(r1.serialize())
    # v21 = evaluate_node.si(v21.serialize())
    # r3 = evaluate_node.si(r3.serialize())
    # v31 = evaluate_node.si(v31.serialize())
    # v32 = evaluate_node.si(v32.serialize())
    # r2 = evaluate_node.si(r2.serialize())


    # layer4 = result
    # layer3 = chord([r2])(layer4)
    # layer2 = chord([r3, v31, v32])(layer3)
    # layer1 = chord([v11, v12, r1, v21])(layer2)

    # print(result)
