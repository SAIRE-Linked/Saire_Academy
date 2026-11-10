"""Original SAIRE teaching material. Not adapted exercises or passages from study guides.

Seed authoring contract: each lesson has explain/demo/guided/independent/check;
outline units deliberately have no lessons. Existing database edits always win.
"""

MODULES = [
    {
        'key': 'IS511', 'position': 1, 'name': 'Information systems in practice',
        'description': 'Turn a service request into useful, minimal, testable information.',
        'outcomes': ['Describe people, process, data and tools in a small service system.',
                     'Translate a request into acceptance criteria.', 'Validate an original Python intake record.'],
        'setup': [
            ('Make a safe practice space', 'Use invented requests only. Create an academy-intake folder. Open it in VS Code. In its terminal run the version command. If py is unavailable, use python throughout.', 'py --version', 'A Python version is printed and no real personal data is present.'),
            ('Try a record', 'In the Python terminal, type this mapping. A dictionary stores named fields; square brackets read one field. Exit with exit(). You will learn the individual steps in the lesson.', 'py\nrequest = {"name": "Library lamp", "priority": 2}\nprint(request["name"])', 'Library lamp is printed. You can explain which field was read.'),
            ('Prepare your evidence', 'Make a notes.txt file with Input, Rule, Output and Evidence headings. Confirm Git works. Nothing in this checklist starts an iteration.', 'git --version', 'Git prints a version; notes.txt exists in the practice folder.'),
        ],
        'lessons': [
            {
                'id': 'it-intake-1', 'title': 'From a request to a system',
                'objective': 'Describe a small service system and write observable acceptance criteria.',
                'explain': 'An information system joins people, agreed steps, recorded facts and tools to achieve a purpose. A spreadsheet alone is a tool; the librarian who checks it and the rule for returning a book are also part of the system. Think of a labelled tray: a request goes in, someone follows a process, and a useful result comes out. The tray analogy helps with the flow, but software also needs permissions, error handling and a record of changes.\n\nOur original example is a neighbourhood repair desk. A volunteer receives a request, checks that it describes one repair, assigns a priority and sends it to a technician. The input is a request; the output is an accepted ticket or a clear rejection. Feedback is what we learn after the technician responds. A failed repair can change the process.\n\nA requirement describes what a system should do. An acceptance criterion says how someone can observe that it did it. “Make it good” is not testable. “Reject a name containing only spaces” is testable. Describe normal, boundary and invalid examples before writing code. Record only what is needed; a repair label does not need someone’s identity number.',
                'demo': 'The desk accepts a repair label and priority. Input: name = " Corridor light ", priority = 2. Rule: remove outside spaces, require a nonempty label and an integer priority from 1 to 3. Output: the cleaned label and priority. Evidence: a test showing the expected record. A request with a blank label should fail with ValueError rather than become a silent empty ticket.\n\nA Python dictionary is a record of named values. Curly braces make it; a key such as "name" labels a value. Reading a missing key raises KeyError. We choose the required fields before reading them. Booleans are a special case: Python treats True as an integer in some operations, but True is not an honest repair priority. Explicitly reject it in the project.',
                'example': 'ticket = {"name": "Corridor light", "priority": 2}\nprint(ticket["name"])\nprint(ticket["priority"])',
                'guided': 'Draw four text columns: Person, Step, Data, Tool. Add the volunteer, validation step, repair label and Python program. Write three acceptance examples, including a blank label. Run the record example and change only the label. Predict the printed result before running it.',
                'independent': 'Design an invented bicycle repair request. Write one normal, one boundary and one invalid example, with exact outputs or errors. Explain one field you deliberately do not collect. Keep this design for the project; do not use personal data.',
                'extra': 'If “system” feels abstract, follow one request from arrival to completion. Ask who acts, what they know and what happens if the information is wrong. A requirement can be written in ordinary language before it becomes code.',
                'checks': [
                    ('Which acceptance criterion can be tested directly?', ['The form feels modern', 'A blank repair label raises ValueError', 'The system is amazing', 'All users are happy'], 1, 'An exact input and observable result allow a repeatable check.'),
                    ('Which item is unnecessary for this repair label record?', ['The repair label', 'A priority', 'A national identity number', 'The validation rule'], 2, 'Collect only information needed for the stated task.'),
                ],
            },
            {
                'id': 'it-intake-2', 'title': 'Validation that explains itself',
                'objective': 'Use dictionary records, string checks and explicit errors to validate inputs.',
                'explain': 'Validation checks whether input follows your rules. Cleaning changes an allowed input into a consistent form. They are different steps: trimming " Desk hinge " is reasonable cleaning; guessing a priority from "urgent-ish" hides an invalid value. Fail clearly instead. A function should have a contract: accepted inputs, returned output and possible errors.\n\nA string is text. strip() returns a new string without outside whitespace. isinstance(value, str) checks the kind of object. Python’s or operator lets us reject either of two bad conditions. Raise ValueError when a supplied value has the wrong meaning for this function. Do not catch every error and return success. That would make broken code look correct.\n\nA dictionary can group a cleaned label and priority so callers read named fields rather than remember positions. A function returning a new dictionary also avoids changing the caller’s data unexpectedly. Unit tests call small functions with chosen inputs and compare the actual result to the contract. Passing local tests is useful feedback; it is not a verified Academy mark.',
                'demo': 'The example validates a location, not the final project implementation. First check the type so that calling strip() is safe. Then reject an empty cleaned value. Return the cleaned text. Calling clean_location("  North shelf  ") returns "North shelf". Calling it with "   " raises ValueError. The caller can show a friendly message and ask for another value.\n\nFor the final intake project, handle priority separately: type(priority) is int excludes True, and a range check handles 0 and 4. Keep your return keys exactly as specified in its README. Write your own tests for the exact endpoints and for the unusual but possible boolean case.',
                'example': 'def clean_location(value):\n    if not isinstance(value, str):\n        raise ValueError("Location must be text")\n    cleaned = value.strip()\n    if not cleaned:\n        raise ValueError("Location is required")\n    return cleaned\n\nprint(clean_location("  North shelf  "))',
                'guided': 'Run clean_location with normal text, spaces and a number. Write the expected result first. Use try/except ValueError only in a small caller that prints a friendly error. Keep the validator itself honest by letting it raise. Explain why the type check comes first.',
                'independent': 'Write and test a clean_category function for an invented donation box. State your allowed categories. Then open the service intake final project after passing this lesson; use its separate contract. Add your own blank, boundary and boolean tests before submission.',
                'extra': 'A raised error stops the current function and looks for a matching handler in its caller. It does not mean every error is a disaster. It is a deliberate way to say that a value cannot be accepted.',
                'checks': [
                    ('Why check a value is text before calling strip()?', ['It guarantees a passing grade', 'It makes every value a string', 'Other object types may not support that operation', 'It deletes the input'], 2, 'Type checks can keep an operation appropriate for its input.'),
                    ('What should an invalid priority produce under this contract?', ['A guessed priority', 'A silent success', 'A zero ticket', 'An explicit ValueError'], 3, 'A clear failure preserves the contract and helps the caller respond.'),
                ],
            },
        ],
        'project': {'slug': 'saire-service-intake', 'file': 'intake.py', 'title': 'Service intake validator',
                    'brief': 'Build make_ticket(name, priority) for a fictional repair desk. Follow the exact contract in the starter README. Validate without guessing and return a fresh named record.',
                    'questions': ['Explain your input and output contract.', 'Why do blank and non-text labels fail?', 'How do you distinguish a boolean from an integer priority?', 'Trace a boundary-case test through your code.', 'Which personal fields did you avoid collecting and why?'],
                    'skills': [('input-validation', 'Input validation', 'tests'), ('systems-thinking', 'Systems thinking', 'defence'), ('readable-code', 'Readable code', 'quality')]},
    },
    {
        'key': 'IS512', 'position': 2, 'name': 'Data and process reliability',
        'description': 'Represent a workflow and report counts without losing or changing input data.',
        'outcomes': ['Represent allowed state changes explicitly.', 'Count records with a dictionary and a loop.', 'Test invalid transitions and preserve the original input.'],
        'setup': [
            ('Revisit your record', 'Complete the intake module and reviewed final project first. In a new workflow-practice folder, make a file with the three labels new, assigned and closed. These are workflow states.', '', 'You can explain the three states in ordinary language.'),
            ('Run a loop', 'A list holds several values. A for loop visits them in order. Run this small sample in Python; use four spaces before print.', 'states = ["new", "assigned", "closed"]\nfor state in states:\n    print(state)', 'Each label prints on a separate line.'),
        ],
        'lessons': [
            {
                'id': 'it-workflow-1', 'title': 'A workflow is a set of promises',
                'objective': 'Represent allowed transitions and reject invalid state changes.',
                'explain': 'A state describes where a request is now. A transition is an allowed move to another state. At our fictional repair desk, new means checked but unassigned, assigned means someone has accepted the job, and closed means the desk recorded a result. These definitions prevent two people from using the same word differently.\n\nWe allow new to assigned, assigned to closed, and closed to new when a repair is reopened. No other moves are allowed in this exercise. In a real service the choices would come from stakeholders, and closing might require evidence. A transition table is like a set of labelled doorways: knowing a room’s name does not mean every door is open. The analogy describes permissions to move, not physical security.\n\nRepresent rules as data when that makes them easier to inspect. A dictionary maps each current state to its permitted next state. Membership checks can first reject an unknown current state. Then compare the requested move with the allowed value. Return a result only after both checks. Do not silently accept spelling mistakes. Exact small rules are easier to test than a long chain of undocumented guesses.',
                'demo': 'Consider a different learning example, a parcel desk. Its permitted steps are received to sorted and sorted to collected. The dictionary is the rule table. The expression current not in routes checks whether a key is absent. routes[current] reads the next allowed label. A short circuit with or prevents reading an absent key. Our final project uses different labels and a reopen rule; do not paste the parcel function as a complete answer.',
                'example': 'def move_parcel(current, target):\n    routes = {"received": "sorted", "sorted": "collected"}\n    if current not in routes or routes[current] != target:\n        raise ValueError("Move not allowed")\n    return target\n\nprint(move_parcel("received", "sorted"))',
                'guided': 'Draw the three repair states as text with arrows. List all nine combinations of current and target; mark exactly three as allowed. Run the parcel example with a valid move, an unknown label and a reverse move. Predict the error before running it.',
                'independent': 'Design a separate two-state borrowed/returned workflow and explain whether returning to the same state should be allowed. Then implement transition(current, target) in the final project using its stated three-state contract. Write one test for every allowed move and two rejected moves.',
                'extra': 'State models describe permitted behaviour. They do not by themselves authenticate a caller or prove a repair happened. Those are separate responsibilities. In the Academy, Django performs the real access checks.',
                'checks': [
                    ('What does a transition rule describe?', ['A permitted change between states', 'A database password', 'A guaranteed repair', 'A file extension'], 0, 'A state model specifies allowed changes.'),
                    ('An unknown state arrives. What follows the project contract?', ['Guess the closest word', 'Close it automatically', 'Ignore the record', 'Raise ValueError'], 3, 'Unknown labels must fail explicitly.'),
                ],
            },
            {
                'id': 'it-workflow-2', 'title': 'Reports that preserve their evidence',
                'objective': 'Count records consistently and explain why a summary is not the whole story.',
                'explain': 'A report is a selected view of data. If a desk has two new tickets and one closed ticket, the counts answer “how many in each state?” They do not prove that the closed repair worked. State the question a report answers and keep the source records available to authorised reviewers. Never invent confidence or completion from a count.\n\nA list is an ordered collection. A for loop reads one item at a time. A dictionary can store a counter for each category. Starting every counter at zero makes an empty report honest: zero closed requests is different from an absent closed field. Add one to the matching counter for each valid record. Reject an unknown state so that a typo does not disappear from the report.\n\nThe report function should leave its input list unchanged. Otherwise a later calculation could see different evidence. This is a small example of separating a calculation from a change to stored data. Use synthetic records during practice. Real information systems also need access rules, retention limits, secure storage and audit trails; those are future lessons, not properties automatically supplied by a Python list.',
                'demo': 'Our example counts shelves rather than repair states. Initialise counters for north and south, then visit each supplied shelf label. counters[label] += 1 means read the existing count and replace it with one more. The empty input produces both zero counts. Invalid labels should be checked before indexing. For the project, validate each record is a dictionary with a known status field, and keep the original records unchanged.',
                'example': 'def count_shelves(labels):\n    counts = {"north": 0, "south": 0}\n    for label in labels:\n        if label not in counts:\n            raise ValueError("Unknown shelf")\n        counts[label] += 1\n    return counts\n\nprint(count_shelves(["north", "south", "north"]))',
                'guided': 'Trace the counter after each item in the sample. Run it with [] and explain every key in the result. Save a copy of the input, run the function, and compare the original with the saved copy. Add a test that rejects "east".',
                'independent': 'Write a report for invented library reservations. Define what it counts and one question it cannot answer. Then implement summary(records) in the workflow project. Include empty input, repeated states, invalid records and an unchanged-input test. Prepare to explain why a count is evidence of recorded states rather than service quality.',
                'extra': 'When a summary surprises you, trace a few source records rather than change the result until it looks right. Write the unexpected example in your private mistakes notebook and revisit it after a short break.',
                'checks': [
                    ('Why include zero counts for known states?', ['To hide missing data', 'To keep the report shape consistent for empty input', 'To claim every repair passed', 'To increase the mark'], 1, 'A stable output contract includes categories even when their count is zero.'),
                    ('What does a closed-ticket count establish?', ['All repairs are high quality', 'All users consented', 'How many records are labelled closed', 'That no errors occurred'], 2, 'The summary answers its stated data question, not every quality question.'),
                ],
            },
        ],
        'project': {'slug': 'saire-workflow-ledger', 'file': 'workflow.py', 'title': 'Workflow ledger',
                    'brief': 'Build transition(current, target) and summary(records) for a fictional repair workflow. Make the rules inspectable, reject invalid records and never alter the supplied list.',
                    'questions': ['Explain each permitted transition.', 'Trace one rejected transition.', 'Why initialise all three counters?', 'How did you verify the input was not changed?', 'What can your report establish, and what can it not establish?'],
                    'skills': [('state-modelling', 'State modelling', 'tests'), ('evidence-reasoning', 'Evidence reasoning', 'defence'), ('readable-code', 'Readable code', 'quality')]},
    },
    {
        'key': 'DB600', 'position': 1, 'name': 'Relational data design: a first slice',
        'description': 'A Year 2 sample: persist a small lending ledger with keys, constraints and safe queries.',
        'outcomes': ['Choose a key and enforce a simple schema in SQLite.', 'Insert text safely using query parameters.', 'Filter rows deterministically and explain an integrity failure.'],
        'setup': [
            ('Confirm prerequisites', 'Finish the shared Python foundation and the two IT foundation modules, including their final projects. Create a separate records-practice folder. This sample is not a complete database course.', '', 'The required modules show completed. Your folder contains only synthetic data.'),
            ('Check the SQLite module', 'Most official CPython installations include sqlite3. It needs no separate database server. If import fails, check your Python distributor’s documentation before reinstalling. Run the command from a terminal.', 'py -c "import sqlite3; print(sqlite3.sqlite_version)"', 'An SQLite version is printed. No database file was downloaded.'),
            ('Open an in-memory database', 'Run this in Python. :memory: makes a temporary database for the current connection. Close it when finished. Never use a production database while learning.', 'import sqlite3\ncon = sqlite3.connect(":memory:")\nprint(con.execute("SELECT 2 + 3").fetchone())\ncon.close()', 'The output contains 5; you can explain that closing loses this temporary database.'),
        ],
        'lessons': [
            {
                'id': 'it-records-1', 'title': 'A table with rules',
                'objective': 'Create a table with a primary key, required fields and constrained values.',
                'explain': 'A relational database stores records in tables. Each row is one record; each column names one kind of fact. A schema states the table’s structure and rules. A primary key identifies a row. It is like a reference number on a labelled drawer: the number helps locate a record, but the database must still enforce uniqueness.\n\nFor a fictional lending desk, a loan needs an integer identifier, an item label and a state. Store each loan once. NOT NULL disallows a missing value, but it does not reject an empty string. A CHECK rule can constrain state to a small agreed set. It is common to use both application validation for helpful messages and database constraints for integrity.\n\nSQLite is an embedded database engine. Python’s sqlite3 module connects to it. SQL is the language used here to define a table and read or change its records. execute sends a statement through a connection. A cursor tracks a statement’s result. An in-memory connection exists only while it stays open. This makes tests quick and separate; it is not durable storage. A real file connection requires explicit attention to commit, rollback, backup and access permissions.',
                'demo': 'The example creates a shelf table, separate from the project’s loans table. The identifier is a primary key and the label is required. Execute the statement once on a fresh connection, then inspect its columns. Attempting a repeated identifier raises sqlite3.IntegrityError. That is the database rejecting an invalid change. Do not swallow the exception and claim the row was stored.\n\nOur project’s create_schema(con) must also be safe to call twice, using CREATE TABLE IF NOT EXISTS. That clause is convenient setup, not a migration strategy for changing an existing production table. Inspect the project README for exact column names and state values.',
                'example': 'import sqlite3\ncon = sqlite3.connect(":memory:")\ncon.execute("CREATE TABLE shelves (id INTEGER PRIMARY KEY, label TEXT NOT NULL)")\nprint(con.execute("PRAGMA table_info(shelves)").fetchall())\ncon.close()',
                'guided': 'Create the shelf table and read the column list. Explain id and label in plain language. Insert one invented shelf using parameters after reading the next demonstration. Try the same id again and record the exception type. Use a new in-memory connection for each fresh experiment.',
                'independent': 'Sketch a table for fictional equipment bookings. Mark its key and required fields, then state one valid and one invalid record. For the loans project, implement create_schema exactly as specified. Verify the permitted states with an actual rejected insert, not just a comment.',
                'extra': 'A primary key identifies a record; it does not describe every business rule. Composite keys, foreign keys, normalisation and multi-table design belong in the remaining database backlog. This slice deliberately uses one table.',
                'checks': [
                    ('Which rule identifies a row uniquely?', ['An optional comment', 'A display colour', 'A primary key', 'A folder name'], 2, 'A primary key supplies row identity and uniqueness.'),
                    ('What does NOT NULL reject?', ['Every blank string', 'A missing SQL NULL value', 'Every duplicate label', 'Every unknown state'], 1, 'NULL and empty text differ; additional rules are needed for the latter.'),
                ],
            },
            {
                'id': 'it-records-2', 'title': 'Queries with safe values and clear results',
                'objective': 'Use placeholders for values, filter rows and return a predictable order.',
                'explain': 'A query asks the database a precise question. SELECT chooses columns, WHERE restricts rows and ORDER BY states an output order. Without ORDER BY you should not depend on the order of results. Make the output contract explicit so another program can use it reliably.\n\nSQL syntax and user values have different jobs. Keep the statement fixed and supply values through placeholders. A question mark is a placeholder in this sqlite3 interface. Pass a tuple of values separately; a single-value tuple needs a trailing comma. Do not glue user text into a statement with an f-string. Parameters handle values, not table or column names; those remain fixed in this project.\n\nA transaction groups changes so they can be committed together or rolled back when a problem occurs. A connection context manager commits on success and rolls back on failure; it does not automatically close the connection. Tests can use an in-memory connection and close it explicitly. Our project functions leave commit and close to their caller. That keeps the transaction boundary visible. Parameterisation does not replace authentication, validation or database file protection.',
                'demo': 'We add a shelf label with a question-mark placeholder, then query shelves by label. The SQL stays fixed even when the text contains an apostrophe. fetchall returns a list of rows; with default sqlite3 settings each row is a tuple. In the project, open_loans returns (id, item) tuples ordered by id, and omits returned loans.\n\nTest with ordinary text, an apostrophe and text that resembles SQL syntax. Treat all of them as literal labels. A safe insert should not damage the table. Check the table remains queryable rather than assuming a lack of an error proves safety.',
                'example': 'import sqlite3\ncon = sqlite3.connect(":memory:")\ncon.execute("CREATE TABLE shelves (id INTEGER PRIMARY KEY, label TEXT NOT NULL)")\ncon.execute("INSERT INTO shelves (id, label) VALUES (?, ?)", (7, "Reader\'s corner"))\nrows = con.execute("SELECT id, label FROM shelves WHERE label = ? ORDER BY id", ("Reader\'s corner",)).fetchall()\nprint(rows)\ncon.close()',
                'guided': 'Run the example and predict the tuple before printing it. Change only the supplied label to include another apostrophe. Explain the trailing comma in the WHERE parameter tuple. Add a second id and use ORDER BY id to check a predictable order.',
                'independent': 'Implement add_loan and open_loans from the starter contract. Test a returned loan is excluded, empty results, sorting, duplicate ids and a label containing SQL-looking text. In your defence, explain the difference between a query value and SQL syntax. Save one failed test in the notebook and revisit it after fixing it.',
                'extra': 'If a database seems to forget changes, check whether it was an in-memory connection or an uncommitted file transaction. Do not test against important files. The revision suggestions in the Academy use recorded checks and notes; they do not infer a hidden skill score from this lesson.',
                'checks': [
                    ('How should a user label be supplied to execute?', ['As a separate parameter value', 'By joining it into SQL text', 'By deleting all spaces', 'As a table name'], 0, 'A placeholder keeps values separate from statement syntax.'),
                    ('Which clause guarantees the requested row order?', ['WHERE', 'NOT NULL', 'SELECT alone', 'ORDER BY'], 3, 'Specify ordering instead of relying on incidental storage order.'),
                ],
            },
        ],
        'project': {'slug': 'saire-lending-records', 'file': 'records.py', 'title': 'Lending records database',
                    'brief': 'Build create_schema(con), add_loan(con, loan_id, item, status) and open_loans(con) using sqlite3. Enforce the schema and insert values safely; return open records in a predictable order.',
                    'questions': ['Explain the primary key and state constraint.', 'Why are placeholders needed for values?', 'Trace an apostrophe-containing item through your insert.', 'Who owns the transaction and connection lifetime?', 'Which database topics remain beyond this one-table design?'],
                    'skills': [('relational-integrity', 'Relational integrity', 'tests'), ('parameterised-sql', 'Parameterised SQL', 'tests'), ('evidence-reasoning', 'Evidence reasoning', 'defence'), ('readable-code', 'Readable code', 'quality')]},
    },
]

# Source-code labels are internal planning identifiers; scopes are honest public summaries.
OUTLINES = [
    ('WEB511', 1, 'Web documents and accessibility', 'Structure semantic HTML, style with CSS, and test keyboard navigation.'),
    ('MATH511', 1, 'Mathematical reasoning for programs', 'Practise arithmetic, algebra, functions, logic and worked reasoning.'),
    ('NET511', 1, 'How computers communicate', 'Trace a local request through devices, layers and protocols.'),
    ('PR512', 1, 'Python collections and application design', 'Use collections, objects, a small interface and persistent records.'),
    ('WEB512', 1, 'Interactive web applications', 'Use JavaScript, DOM events, forms and explicit browser error handling.'),
    ('MATH512', 1, 'Change, accumulation and models', 'Build from equations and functions to limits, derivatives and integrals.'),
    ('NET512', 1, 'Secure and connected systems', 'Reason about network threats, addressing, mobile networks and cloud connectivity.'),
    ('DS500', 1, 'Data questions and trustworthy analysis', 'Describe data, clean it, visualise it and evaluate simple statistical claims.'),
    ('PR621', 2, 'Software structures and algorithms', 'Design larger programs and justify algorithm and data-structure choices.'),
    ('PR622', 2, 'Maintainable application engineering', 'Test, refactor and document a multi-component application.'),
    ('IP621', 2, 'Web services and persistence', 'Connect web requests, validation, services and persistent data.'),
    ('IP622', 2, 'Reliable web delivery', 'Test authentication, errors and deployment of a web service.'),
    ('IS621', 2, 'Investigating information systems', 'Elicit requirements and model processes with traceable evidence.'),
    ('IS622', 2, 'Designing useful information systems', 'Compare designs, evaluate usability and plan responsible change.'),
    ('CC600', 2, 'Cloud systems and operations', 'Explain shared responsibility, deployment choices, costs and recovery.'),
    ('ML600', 2, 'Machine learning with evidence', 'Separate training and evaluation, establish baselines and examine failure.'),
    ('BDI600', 2, 'Connected data and devices', 'Reason about telemetry, streaming, storage, privacy and device failure.'),
]

# Before/after practice checks use distinct questions from the graded lesson quiz.
PRACTICE = {
 'it-intake-1': [
  ('A volunteer checks a request and writes its repair label. Which part is the process?', ['The checking step', 'The label text', 'The keyboard'], 0, 'A process is the agreed activity performed on the request.'),
  ('Which invented example checks a boundary of a 1–3 priority rule?', ['Priority 2 only', 'Priority 3', 'A different font'], 1, 'The endpoint 3 is an allowed boundary; test just outside it too.'),
 ],
 'it-intake-2': [
  ('What does "  Door  ".strip() produce?', ['"  Door  "', 'An empty string', '"Door"'], 2, 'strip removes outside whitespace and returns a new string.'),
  ('Your validator returns a new record. What should happen to the caller’s original data?', ['It stays unchanged', 'It is silently deleted', 'It must become global'], 0, 'Separate validation results from unexpected changes to the caller’s data.'),
 ],
 'it-workflow-1': [
  ('A parcel is sorted. In the demonstration, which next state is permitted?', ['received', 'collected', 'unknown'], 1, 'The example rule table allows sorted to collected.'),
  ('A workflow diagram shows no arrow from A to C. What should a strict implementation do with A to C?', ['Invent the arrow', 'Skip validation', 'Reject the move'], 2, 'An absent permitted route is an invalid transition under the explicit model.'),
 ],
 'it-workflow-2': [
  ('A report counts [north, north, south]. How many north entries are recorded?', ['2', '3', '0'], 0, 'Trace one increment for each of the two north entries.'),
  ('A report function changes the supplied list while counting it. Why is that a problem?', ['Reports must be colourful', 'A later calculation may see changed evidence', 'A count can never be computed'], 1, 'Unexpected mutation changes what later callers can inspect.'),
 ],
 'it-records-1': [
  ('Two rows use the same INTEGER PRIMARY KEY value. What should SQLite do?', ['Store both quietly', 'Rename the column', 'Reject the duplicate'], 2, 'The primary key must uniquely identify a row.'),
  ('You close an in-memory database connection. Where is that temporary database now?', ['It has been lost with that connection', 'Automatically saved in the cloud', 'Attached to every future connection'], 0, 'An in-memory database is tied to its connection lifetime.'),
 ],
 'it-records-2': [
  ('Which one-element parameter tuple is valid Python?', ['("Desk")', '("Desk",)', '"Desk", "Lamp"'], 1, 'The trailing comma makes a one-element tuple.'),
  ('A query returns no matching loans. What does fetchall() return?', ['A fabricated loan', 'A passing grade', 'An empty list'], 2, 'No matching records means an empty result, not an invented record.'),
 ],
}
