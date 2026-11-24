def create_schema(con):
    """Create loans(id INTEGER PRIMARY KEY, item TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('open', 'returned'))).
    Use IF NOT EXISTS; leave commit/close to the caller. No other schema required.
    """
    raise NotImplementedError("Implement this contract")

def add_loan(con, loan_id, item, status):
    """loan_id: exactly int (not bool), >0. item: str, strip and require nonempty.
    status: str, exactly open or returned. Invalid inputs raise ValueError.
    INSERT with parameters. A duplicate id propagates sqlite3.IntegrityError.
    Return None. Do not commit, close or replace an existing row.
    """
    raise NotImplementedError("Implement this contract")

def open_loans(con):
    """Return [(id, item), ...] for open loans only, sorted by id ascending.
    Leave connection and transaction open for the caller. Empty returns [].
    """
    raise NotImplementedError("Implement this contract")
