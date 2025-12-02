class ContactStore:
    def __init__(self):
        self._contacts = {}

    def add_contact(self, contact: dict):
        self._contacts[contact["public_key"]] = contact

    def get_contact(self, pubkey: str) -> dict | None:
        return self._contacts.get(pubkey)

    def all_contacts(self) -> list[dict]:
        return list(self._contacts.values())

    def remove_contact(self, pubkey: str):
        self._contacts.pop(pubkey, None)
