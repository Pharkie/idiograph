"""The family's one error (22 October 2026, the family codebase's second build).

Every app's refusal, a line the person reads and acts on, shown in the interface as written, is one
class, so the server, the command line and the MCP server answer any app's in the same way. It keeps
its old name, `WorkbookError`, which every module and area catches it by and a refusal is named by, and
`AppError` is the same class by the family's name. Each app's own refusals are its subclasses, Sift's
`SiftError`, Trace's `TraceError`, and the screening reader's here, `ScreeningError`.

A refusal that a script reacts to carries a code beside its words (i18ncodes, 31 October 2026), one of
`CODES`, so the page and the server's own modules test what was refused and never how a language words
it. The server's answer gives it as `code` beside `error` (`refusal`), and the words stay for the person,
agents and logs.

The standard library only.
"""
from __future__ import annotations

# Every code a refusal carries, and what it means. A code is a fixed word in the API, never translated and
# never shown: the page tests it (shell.js `refusedAs`), and so does a module of the server's that catches a
# refusal of another's. A refusal no script reacts to carries none.
CODES = {
    "no_endpoint": "the server has no such route, so it is older than the page that asked",
    "unknown_op": "the route has no such op, so the server is older than the page that asked",
    "board_changed_outside": "the board changed in a conversation, so the canvas was kept in its History, not saved",
    "file_not_held": "the file a card sent earlier is no longer held, so it is to be sent whole again",
    "busy": "another write holds the files' lock, so nothing was written",
    "not_yours": "in a project worked on together another member works on that participant or GETs board",
    "zotero_storage_full": "the Zotero library's file storage is full, so no more PDFs go up",
    # the agent log's (noholds, 13 November 2026): an op only the app does, refused for an agent, and the note of the
    # actions that waited for his yes, cleared when approvals were removed
    "app_only": "only the app does it, since no undo reaches it, so an agent was refused and nothing waits",
    "cleared": "the actions that waited for his yes were dropped when approvals were removed, a note and no refusal",
}


class WorkbookError(Exception):
    """Something the person needs to read and act on, shown in the interface as written, and `code`, one of
    `CODES`, where a script reacts to it."""

    code = ""

    def __init__(self, *args, code: str = ""):
        super().__init__(*args)
        if code:
            self.code = code


# the family's name for it, the same class, which an app's own refusals take as their base
AppError = WorkbookError


class ScreeningError(AppError):
    """A screening of Sift's that cannot be read, said in one plain line (`screenings.py`)."""


def refusal(exc: BaseException) -> dict:
    """A refusal as the server answers it: its words as `error`, and its code beside them when it has one."""
    code = getattr(exc, "code", "")
    return {"error": str(exc), "code": code} if code else {"error": str(exc)}
