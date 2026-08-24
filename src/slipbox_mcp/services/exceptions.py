"""Typed exceptions for the service layer.

These subclass ValueError so existing ``except ValueError`` handling and the
server's error formatter keep treating them as user-facing validation errors,
while giving callers a specific type to catch when they need to.
"""


class NoteNotFoundError(ValueError):
    """Raised when a note lookup by ID returns nothing.

    ``label`` varies the message to name the missing note's role (e.g. "Source
    note", "Target note") while keeping one exception type to catch.
    """

    def __init__(self, note_id: str, label: str = "Note"):
        super().__init__(f"{label} with ID {note_id} not found")
