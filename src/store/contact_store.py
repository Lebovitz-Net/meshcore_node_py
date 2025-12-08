# store/contact_store.py
# ContactStore provides convenience functions into the generalized StorageManager.
# It wraps the singleton StorageManager and specializes for "contacts".

from store.storage_manager import StorageManager

class ContactStore:
    def __init__(self):
        # Always use the singleton StorageManager
        self._store = StorageManager()
        # Ensure the "contacts" data type exists
        self._store.add_data_type("contacts")

    def add_contact(self, contact: dict):
        """
        Add or update a contact.
        The contact dict must include a "public_key" field.
        """
        pubkey = contact.get("public_key")
        if not pubkey:
            raise ValueError("Contact must include a 'public_key'")
        self._store.add_data("contacts", contact)

    def get_contact(self, pubkey: str) -> dict | None:
        """
        Retrieve a contact by its public key.
        Returns None if not found.
        """
        contacts = self._store.all_data("contacts")
        for c in contacts:
            if c.get("public_key") == pubkey:
                return c
        return None

    def all_contacts(self) -> list[dict]:
        """
        Return all contacts as a list of dicts.
        """
        return self._store.all_data("contacts")

    def remove_contact(self, pubkey: str):
        """
        Remove a contact by its public key.
        """
        contacts = self._store.all_data("contacts")
        for idx, c in enumerate(contacts):
            if c.get("public_key") == pubkey:
                self._store.remove_data("contacts", idx)
                break

    def clear_contacts(self):
        """
        Clear all contacts.
        """
        self._store.clear_data("contacts")
