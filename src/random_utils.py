import random

class RandomUtils:
    @staticmethod
    def get_random_int(min_val: int, max_val: int) -> int:
        """
        Return a random integer between min_val and max_val inclusive.
        Equivalent to JS Math.floor(Math.random() * (max - min + 1)) + min.
        """
        return random.randint(min_val, max_val)
