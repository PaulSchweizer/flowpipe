"""Recipients and Text are needed for sending an email.

+----------+
|recipients+------------+
+----------+           |
                 +-----v----+
                 |email     |
                 +-----^----+
+----------+           |
|text      +-----------+
+----------+

"""
from __future__ import print_function

from flowpipe.node import FlowNode
from flowpipe.app import FlowApp
from flowpipe.engine import FlowEngine

# ---------------------------------------------------------------------
# The nodes needed for the app
# ---------------------------------------------------------------------

class ValueNode(FlowNode):
    """Very basic node, just holding a simple value."""

    flow_ins = ['value']
    flow_outs = ['value']

    def __init__(self, value=None):
        super(ValueNode, self).__init__()
        self.value = value

    def compute(self):
        pass


class EmailNode(FlowNode):
    """Send an email."""

    flow_ins = ['recipients', 'text']

    def __init__(self):
        super(EmailNode, self).__init__()
        self.text = ''
        self.recipients = list()

    def compute(self):
        print('Sending Email to:', self.recipients, self.text)


# ---------------------------------------------------------------------
# The app holds the node network
# ---------------------------------------------------------------------

class EmailApp(FlowApp):
    """Send an email."""

    def __init__(self, recipients, text):
        # Build the network
        recipients = ValueNode(recipients)
        text = ValueNode(text)
        email = EmailNode()

        # Connect the nodes
        recipients.connect('value', email, 'recipients')
        text.connect('value', email, 'text')

        self.nodes = [recipients, text, email]

email_app = EmailApp(['Me', 'You', 'Her'], 'The Text of the email')

engine = FlowEngine()
engine.load_app(email_app)

# engine.evaluate()


# ---------------------------------------------------------------------
# Publishing an Asset
# ---------------------------------------------------------------------


class NextVersion(FlowNode):

    flow_ins = ['asset']
    flow_outs = ['next_version']

    def compute(self):
        self.next_version = 'NextVersion'


class SaveFile(FlowNode):

    flow_ins = ['asset_file']

    def compute(self):
        self.saved_asset_file = self.asset_file


class SaveNotes(FlowNode):

    flow_ins = ['notes', 'asset_file']

    def compute(self):
        pass

class SaveToUnity(FlowNode):

    flow_ins = ['asset_file']

    def compute(self):
        pass


class Publish(FlowNode):

    flow_ins = ['asset']
    flow_outs = ['published_file']

    def compute(self):
        self.published_file = self.asset.next_version


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


class PublisherApp(FlowApp):
    """Publish a new version of an Asset."""

    def __init__(self, asset, notes):
        """@todo documentation for __init__."""

        # Build the network
        next_version = NextVersion()
        save_file = SaveFile()
        save_notes = SaveNotes()
        save_to_unity = SaveToUnity()

        self.nodes = [next_version, save_file, save_notes, save_to_unity]

        # Connect the nodes
        next_version.connect('next_version', save_file, 'asset_file')
        next_version.connect('next_version', save_notes, 'asset_file')
        next_version.connect('next_version', save_to_unity, 'asset_file')

        # Set the initial values
        next_version.asset = asset
        save_notes.notes = notes
    # end def __init__
# end class PublisherApp


asset = {'project': 'MyProject', 'name': 'Tiger', 'kind': 'model'}
notes = 'MyNotes'


publisher_app = PublisherApp(asset, notes)


engine = FlowEngine()

engine.load_app(publisher_app)

engine.evaluate()

engine.evaluate()




















