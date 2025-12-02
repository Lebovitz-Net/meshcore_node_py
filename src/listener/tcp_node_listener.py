# tcp_node_listener.py
from src.listener.node_listener import NodeListener
from src.listener.tcp_transport import TCPTransport

class TCPNodeListener(NodeListener):
    def __init__(self, host="0.0.0.0", port=9000,
                 contact_store=None, message_store=None):
        transport = TCPTransport(host, port)
        super().__init__(transport,
                         contact_store=contact_store,
                         message_store=message_store)

