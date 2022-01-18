"""Two simple examples from the README file.

Build a house:

+------------------------+          +------------------------+          +---------------------------+
|      HireWorkers       |          |       Build Roof       |          |    Housewarming Party     |
|------------------------|          |------------------------|          |---------------------------|
o amount<4>              |          o section<"roof">        |          % attendees                 |
|                workers %          % workers                |     +--->o  attendees.0<>            |
|             workers.0  o-----+--->o  workers.0<>           |     |--->o  attendees.1<>            |
|             workers.1  o-----|--->o  workers.1<>           |     |--->o  attendees.2<>            |
|             workers.2  o-----|    |                workers %     |--->o  attendees.3<>            |
|             workers.3  o-----|    |             workers.0  o-----|    o  attendees.4<"Homeowner>  |
+------------------------+     |    |             workers.1  o-----|    +---------------------------+
                               |    +------------------------+     |
                               |    +------------------------+     |
                               |    |      Build Walls       |     |
                               |    |------------------------|     |
                               |    o section<"walls">       |     |
                               |    % workers                |     |
                               +--->o  workers.0<>           |     |
                               +--->o  workers.1<>           |     |
                                    |                workers %     |
                                    |             workers.0  o-----+
                                    |             workers.1  o-----+
                                    +------------------------+

Throw a birthday party:

+-------------------+          +---------------------+
|   InvitePeople    |          |   Birthday Party    |
|-------------------|          |---------------------|
o amount<4>         |     +--->o attendees<>         |
|            people o-----+    +---------------------+
+-------------------+

"""
from flowpipe import Graph, INode, InputPlug, Node, OutputPlug


class HireWorkers(INode):
    """A node can be derived from the INode interface.

    The plugs are defined in the init method.
    The compute method received the inputs from any connected upstream nodes.
    """

    def __init__(self, amount=None, **kwargs):
        super(HireWorkers, self).__init__(**kwargs)
        InputPlug("amount", self, amount)
        OutputPlug("workers", self)

    def compute(self, amount):
        workers = ["John", "Jane", "Mike", "Michelle"]
        print("{0} workers are hired to build the house.".format(amount))
        return {"workers.{0}".format(i): workers[i] for i in range(amount)}


@Node(outputs=["workers"])
def Build(workers, section):
    """A node can also be created by the Node decorator.outputs

    The inputs to the function are turned into InputsPlugs, outputs are defined
    in the decorator itself.
    The wrapped function is used as the compute method.
    """
    print(
        "{0} are building the {1}".format(", ".join(workers.values()), section)
    )
    return {"workers.{0}".format(i): worker for i, worker in workers.items()}


@Node()
def Party(attendees):
    """Nodes do not necessarily need to have output or input plugs."""
    print(
        "{0} and {1} are having a great party!".format(
            ", ".join(list(attendees.values())[:-1]),
            list(attendees.values())[-1],
        )
    )


graph = Graph(name="Build a House")
workers = HireWorkers(graph=graph, amount=4)
build_walls = Build(graph=graph, name="Build Walls", section="walls")
build_roof = Build(graph=graph, name="Build Roof", section="roof")
party = Party(graph=graph, name="Housewarming Party")

# Nodes are connected via their input/output plugs.
workers.outputs["workers"]["0"].connect(build_walls.inputs["workers"]["0"])
workers.outputs["workers"]["1"].connect(build_walls.inputs["workers"]["1"])
workers.outputs["workers"]["2"].connect(build_roof.inputs["workers"]["0"])
workers.outputs["workers"]["3"].connect(build_roof.inputs["workers"]["1"])

# Connecting nodes can be done via the bit shift operator as well
build_walls.outputs["workers"]["0"] >> party.inputs["attendees"]["0"]
build_walls.outputs["workers"]["1"] >> party.inputs["attendees"]["2"]
build_roof.outputs["workers"]["0"] >> party.inputs["attendees"]["1"]
build_roof.outputs["workers"]["1"] >> party.inputs["attendees"]["3"]

# Initial values can be set onto the input plugs for initialization
party.inputs["attendees"]["4"].value = "Homeowner"


print("---------------------------------------")
print(graph.name)
print(graph)
print(graph.list_repr())
print("---------------------------------------")
graph.evaluate()
print("---------------------------------------")


graph = Graph(name="Celebrate a Birthday Party")


@Node(outputs=["people"])
def InvitePeople(amount):
    people = ["John", "Jane", "Mike", "Michelle"]
    d = {"people.{0}".format(i): people[i] for i in range(amount)}
    d["people"] = {people[i]: people[i] for i in range(amount)}
    return d


invite = InvitePeople(graph=graph, amount=4)
birthday_party = Party(graph=graph, name="Birthday Party")
invite.outputs["people"] >> birthday_party.inputs["attendees"]


print("---------------------------------------")
print(graph.name)
print(graph)
print("---------------------------------------")
graph.evaluate()
print("---------------------------------------")
