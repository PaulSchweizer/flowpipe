"""Showing a programming pattern that defines plug names at runtime.

In some applications it will be useful to re-use the same node definition for
different inputs/output - our working example will be to compute a face match.
To do so, we use an `EmbeddingNode` to compute features from both, an input
and a reference image, and then a `MatchNode` to compute whether the faces are
the same from these embeddings.

If the graph is to remain both, clean and explicit, it is advantageous to name
the plugs differently for the different `EmbeddingNode`.

To do so, accept the plug names as parameters to the nodes `__init__()` method.
You can then define the InputPlugs / OutputPlug with the given name. To access
the dynamically named plugs, your INode instance needs to store the plug names
as attributes, and the `compute()` method needs to allow for generic keyword
arguments.
"""

from flowpipe import Graph, INode, InputPlug, OutputPlug


def compute_embeddings(image):
    """A mock function for a call to a deep learning model or a web service."""
    del image  # this is just a mock and doesn't do anything with the input
    return 42


def compare_embeddings(image_emb, reference_emb, threshold=2):
    """A mock function for the appropriate comparison of embeddings."""
    return abs(image_emb - reference_emb) < threshold


class EmbeddingNode(INode):
    """The embedding node computes facial features from an image."""

    def __init__(self, input_name, output_name, **kwargs):
        """Set up a new EmbeddingNode with given names for plugs."""
        super().__init__(**kwargs)

        self.input_name = input_name  # Needed to access the value in compute
        InputPlug(input_name, self)

        self.output_name = output_name  # Needed to access the value in compute
        OutputPlug(output_name, self)

    # Accept generic keyword arguments, since the names of the inputs are
    # undefined until at runtime
    def compute(self, **kwargs):
        image = kwargs.pop(self.input_name)

        embedding = compute_embeddings(image)

        return {self.output_name: embedding}


class MatchNode(INode):
    """The match node compares two embeddings."""

    def __init__(self, threshold=2, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold

        InputPlug("image_emb", self)
        InputPlug("reference_emb", self)

        OutputPlug("facematch", self)

    def compute(self, image_emb, reference_emb):
        """Compare the embeddings."""
        match = compare_embeddings(image_emb, reference_emb, self.threshold)
        return {"facematch": match}


def get_facematch_graph(threshold):
    """Set up facematching e.g. with paramters taken from a config."""
    facematch_graph = Graph()

    #It is useful to define
    image_node = EmbeddingNode(input_name="image",
                               output_name="image_emb",
                               graph=facematch_graph,
                               name="ImageEmbeddings")

    reference_node = EmbeddingNode(input_name="reference",
                                   output_name="reference_emb",
                                   graph=facematch_graph,
                                   name="ReferenceEmbeddings")

    match_node = MatchNode(threshold=threshold,
                           graph=facematch_graph)

    image_node.outputs["image_emb"] >> match_node.inputs["image_emb"]
    reference_node.outputs["reference_emb"] \
        >> match_node.inputs["reference_emb"]

    match_node.outputs["facematch"].promote_to_graph("result")

    return facematch_graph


if __name__ == "__main__":
    facematch = get_facematch_graph(1)

    image = "foo"  # load image from disk
    reference = "bar"  # load image from database
    facematch.evaluate(mode="threading")

    print(facematch)
    print("\n", facematch.outputs["result"].value)

