# storage/message_store.py
# MessageStore provides convenience functions into the generalized StorageManager.
# It does not need to inherit from StorageManager; instead, it wraps the singleton instance.
# This keeps StorageManager generic and allows MessageStore to specialize for "messages".

from .storage_manager import StorageManager

class MessageStore:
    def __init__(self):
        # Always use the singleton StorageManager
        self._store = StorageManager()
        # Ensure the "messages" data type exists
        self._store.add_data_type("messages")

    def add_message(self, message):
        """Add a message to the store."""
        self._store.add_data("messages", message)

    def all_messages(self):
        """Return all messages."""
        return self._store.all_data("messages")

    def get_message(self, index: int):
        """Get a specific message by index."""
        return self._store.get_data("messages", index)

    def remove_message(self, index: int):
        """Remove a specific message by index."""
        self._store.remove_data("messages", index)

    def clear_messages(self):
        """Clear all messages."""
        self._store.clear_data("messages")
