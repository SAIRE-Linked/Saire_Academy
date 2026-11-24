def make_ticket(name, priority):
    """Return a fresh {"name": cleaned_name, "priority": priority} dictionary.

    name: str, strip outside whitespace, then require 1..80 characters inclusive.
    priority: exactly int (not bool), from 1 to 3 inclusive.
    Raise ValueError for every invalid input. Do not coerce values.
    """
    raise NotImplementedError("Implement this contract")
