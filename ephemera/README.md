# ephemera/

Whole-session Claude Code ephemera snapshots — the auditability law's home in autoharn
([C13]). `filing/persist_claude_ephemera.py` targets this directory. Snapshots are
whole-session, never cherry-picked (deciding what is "worth keeping" is how audit trails
get holes). Claude Code keys ephemera by working-directory slug, so sessions run from
autoharn write a new slug; never assert a piece is lost until every slug the session used
has been searched.
