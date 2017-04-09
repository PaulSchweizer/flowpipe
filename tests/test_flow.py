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

engine.evaluate()
