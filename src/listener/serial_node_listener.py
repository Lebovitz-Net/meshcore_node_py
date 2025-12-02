# serial_node_listener.py
from listener.node_listener import NodeListener
from listener.serial_transport import SerialTransport

class SerialNodeListener(NodeListener):
    def __init__(self, port="/dev/ttyS0", baudrate=9600,
                 contact_store=None, message_store=None):
        transport = SerialTransport(port, baudrate)
        super().__init__(transport, contact_store=contact_store, message_store=message_store)
