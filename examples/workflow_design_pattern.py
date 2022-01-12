"""Demonstration of the Workflow Design Pattern.

As the name suggests, this pattern wants to represent workflows.
It is basically an extension of the 'Command Pattern' meant for more complex,
long-running commands consisting of multiple sub-commands. Workflows also
provide multiple ways of evaluation, usually local and remote.

A workflow would be a common, pre-defined set of tasks frequently used in a
pipeline, for example:
    - prepare a delivery to the client
    - publish geometry with a subsequent turntable rendering
    - ingest data from vendors, including data cleanup and transformation

The Workflow builds a Graph and initializes it with user provided settings as
well as data taken from other sources (database, filesystem).
"""
import getpass

from flowpipe import Graph, Node


class Workflow(object):
    """Abstract base class defining a workflow, based on a flowpipe graph.

    The Workflow holds a graph and provides two ways to evaluate the graph,
    locally and remotely.
    """

    def __init__(self):
        self.graph = Graph()

    def evaluate_locally(self):
        """Evaluate the graph locally."""
        self.graph.evaluate()

    def evaluate_remotely(self):
        """See examples/vfx_render_farm_conversion.py on how to implement a
        conversion from flowpipe graphs to your render farm.
        """
        pass


class PublishWorkflow(Workflow):
    """Publish a model and add a turntable render of it to the database."""

    def __init__(self, source_file):
        super(PublishWorkflow, self).__init__()
        publish = Publish(graph=self.graph)
        message = SendMessage(graph=self.graph)
        turntable = CreateTurntable(graph=self.graph)
        update_database = UpdateDatabase(graph=self.graph)
        publish.outputs["published_file"].connect(
            turntable.inputs["alembic_cache"]
        )
        publish.outputs["published_file"].connect(
            message.inputs["values"]["path"]
        )
        turntable.outputs["turntable"].connect(
            update_database.inputs["images"]
        )

        # Initialize the graph from user input
        publish.inputs["source_file"].value = source_file

        # Initialize the graph through pipeline logic
        # These things can also be done in the nodes themselves of course,
        # it's a design choice and depends on the case
        message.inputs["template"].value = (
            "Hello,\n\n"
            "The following file has been published: {path}\n\n"
            "Thank you,\n\n"
            "{sender}"
        )
        message.inputs["values"]["sender"].value = getpass.getuser()
        message.inputs["values"]["recipients"].value = [
            "john@mail.com",
            "jane@mail.com",
        ]
        turntable.inputs["render_template"].value = "template.ma"
        update_database.inputs["asset"].value = source_file.split(".")[0]
        update_database.inputs["status"].value = "published"


# -----------------------------------------------------------------------------
#
# The Nodes used in the Graph
#
# -----------------------------------------------------------------------------


@Node(outputs=["published_file"])
def Publish(source_file):
    """Publish the given source file."""
    return {"published_file": "/published/file.abc"}


@Node(outputs=["return_status"])
def SendMessage(template, values, recipients):
    """Send message to given recipients."""
    print("--------------------------------------")
    print(template.format(**values))
    print("--------------------------------------")
    return {"return_status": 0}


@Node(outputs=["turntable"])
def CreateTurntable(alembic_cache, render_template):
    """Load the given cache into the given template file and render."""
    return {"turntable": "/turntable/turntable.%04d.jpg"}


@Node(outputs=["asset"])
def UpdateDatabase(asset, images, status):
    """Update the database entries of the given asset with the given data."""
    return {"asset": asset}


if __name__ == "__main__":
    workflow = PublishWorkflow("model.ma")
    print(workflow.graph)
    workflow.evaluate_locally()
