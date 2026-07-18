#!/usr/bin/env python3
"""rename_schemas.py -- rehearsal-restore renamer for the ent s29 in-place migration.

Reads a plain-format pg_dump on stdin, renames schema identifiers ent -> s29reh and
ent_kernel -> s29reh_kernel, writes the result on stdout. The rename is applied ONLY
outside COPY data blocks: ledger row content (which may legitimately contain the word
"ent") is passed through byte-for-byte, so the scratch restore's data is provably
identical to the dump's. Word-boundary regex, so the ROLE names ent_rw/ent_ro/ent_owner
(underscore is a word character) are never touched -- grants restore against the real
roles, which is what lets ./verify-chain SET ROLE ent_rw against the scratch pair.
"""
import re
import sys

RE_KERN = re.compile(r"\bent_kernel\b")
RE_SCHEMA = re.compile(r"\bent\b")

in_copy = False
for line in sys.stdin:
    if in_copy:
        if line.rstrip("\n") == "\\.":
            in_copy = False
        sys.stdout.write(line)
        continue
    renamed = RE_SCHEMA.sub("s29reh", RE_KERN.sub("s29reh_kernel", line))
    sys.stdout.write(renamed)
    if renamed.startswith("COPY ") and renamed.rstrip().endswith("FROM stdin;"):
        in_copy = True
