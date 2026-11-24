def transition(current, target):
    """Both inputs must be str. Allowed: new->assigned, assigned->closed, closed->new.
    Return target for an allowed move. All others raise ValueError (including
    unknown, non-text, or identical states). No automatic correction.
    """
    raise NotImplementedError("Implement this contract")

def summary(records):
    """records must be a list of dicts with a status in new/assigned/closed.
    Extra dictionary keys are allowed. Return all three counts as a fresh dict.
    Empty list returns zero counts. Missing/invalid states, non-dict elements,
    non-text status and non-list input raise ValueError. Never mutate records.
    """
    raise NotImplementedError("Implement this contract")
