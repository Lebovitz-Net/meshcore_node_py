class MessageStore:
    def __init__(self):
        self._messages = []

    def add_message(self, msg: dict):
        self._messages.append(msg)

    def all_messages(self) -> list[dict]:
        return self._messages

    def get_messages_for_contact(self, pubkey_prefix: str) -> list[dict]:
        return [m for m in self._messages if m.get("pubkey_prefix") == pubkey_prefix]

    def get_messages_for_channel(self, channel_idx: int) -> list[dict]:
        return [m for m in self._messages if m.get("channel_idx") == channel_idx]
