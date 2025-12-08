# storage/store.py
# Generalized singleton storage manager with dynamic data types.
# Data types are referenced by string keys (e.g. "contacts", "messages").

import threading

class StorageManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StorageManager, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        # Dictionary of data types -> list or dict of items
        self._data = {}

    # --- Data type management ---
    def add_data_type(self, type_name: str):
        """Create a new data type container if it doesn't exist."""
        if type_name not in self._data:
            self._data[type_name] = []

    def remove_data_type(self, type_name: str):
        """Remove an entire data type and its contents."""
        if type_name in self._data:
            del self._data[type_name]

    # --- Data operations ---
    def add_data(self, type_name: str, item):
        """Add an item to a given data type."""
        if type_name not in self._data:
            self.add_data_type(type_name)
        self._data[type_name].append(item)

    def all_data(self, type_name: str):
        """Return all items for a given data type."""
        return list(self._data.get(type_name, []))

    def get_data(self, type_name: str, index: int):
        """Get a specific item by index from a data type."""
        items = self._data.get(type_name, [])
        if 0 <= index < len(items):
            return items[index]
        return None

    def clear_data(self, type_name: str):
        """Clear all items from a given data type."""
        if type_name in self._data:
            self._data[type_name].clear()

    def remove_data(self, type_name: str, index: int):
        """Remove a specific item by index from a data type."""
        items = self._data.get(type_name, [])
        if 0 <= index < len(items):
            items.pop(index)

    # --- Utility ---
    def list_types(self):
        """Return all defined data types."""
        return list(self._data.keys())
