#!/usr/bin/env python3
"""Statically enumerate EVERY pickled global a torch .ckpt references.

Run ONCE on the host where the .ckpt lives. Executes NO pickle bytecode: it
disassembles the pickle opcode stream with pickletools and reconstructs the
(module, name) operands of GLOBAL and STACK_GLOBAL by tracking string pushes
and the memo. The output is the COMPLETE, definitive set of globals the
checkpoint needs to unpickle -- the audited allowlist, with no host round-trip
guessing (ADR-0013: one round-trip, total information, no grind).

Audit rule for the "MUST be audited" bucket (per the ADR-0014 second opinion):
ALLOWLIST only pure-DATA types (containers/scalars, omegaconf config nodes whose
__setstate__ merely assigns fields). REFUSE anything callable-with-side-effects
(os/subprocess/socket/eval/exec/getattr/__import__/functools.partial/...) or any
class whose __reduce__ reconstructs via a different callable -- a refusal is proof
the file is not what you think (ADR-0002 fail loud), never a thing to append.

Usage:  python enumerate_ckpt_globals.py /path/to/weights.ckpt
"""
import sys
import zipfile
import pickletools


_STR_OPS = {
    "SHORT_BINUNICODE", "BINUNICODE", "BINUNICODE8",
    "SHORT_BINSTRING", "BINSTRING", "STRING", "UNICODE",
}
_GET = {"GET", "BINGET", "LONG_BINGET"}


def globals_in_pickle(data: bytes):
    """Return sorted set of (module, name) referenced by GLOBAL/STACK_GLOBAL."""
    found = set()
    stack = []          # symbolic value stack (only strings matter; else None)
    memo = {}           # memo idx -> value
    next_memo = 0
    for op, arg, _pos in pickletools.genops(data):
        name = op.name
        if name in _STR_OPS:
            stack.append(arg)
        elif name == "MEMOIZE":
            memo[next_memo] = stack[-1] if stack else None
            next_memo += 1
        elif name in ("PUT", "BINPUT", "LONG_BINPUT"):
            memo[int(arg)] = stack[-1] if stack else None
        elif name in _GET:
            stack.append(memo.get(int(arg)))
        elif name == "GLOBAL":
            mod, _, nm = arg.partition("\n")  # protocol <2: "module\nname"
            found.add((mod, nm))
            stack.append(None)
        elif name == "STACK_GLOBAL":
            nm = stack.pop() if stack else None
            mod = stack.pop() if stack else None
            found.add((mod, nm))
            stack.append(None)
        else:
            if op.stack_after and not op.stack_before:
                stack.append(None)
    return sorted(found, key=lambda t: (t[0] or "", t[1] or ""))


def find_data_pkl(zf: zipfile.ZipFile):
    """The torch zip stores the object graph in <archive>/data.pkl. Storage tensor
    bytes live under <archive>/data/<n> and are NOT pickles."""
    cands = [n for n in zf.namelist() if n.rsplit("/", 1)[-1] == "data.pkl"]
    if not cands:
        raise SystemExit("no data.pkl member found; not a torch zip checkpoint?")
    if len(cands) > 1:
        print(f"# note: multiple data.pkl members, scanning all: {cands}")
    return cands


def torch_builtin_allowed():
    """Globals torch's weights_only unpickler ALREADY permits (subtract them: no
    action needed). Empty set if torch unavailable."""
    try:
        import torch.serialization as ts
    except Exception:
        return set()
    out = set()
    getter = getattr(ts, "_get_allowed_globals", None)
    if getter:
        for k in getter().keys():   # keys are "module.qualname" strings
            mod, _, nm = k.rpartition(".")
            out.add((mod, nm))
    return out


def main(path):
    builtin = torch_builtin_allowed()
    with zipfile.ZipFile(path) as zf:
        all_globals = set()
        for member in find_data_pkl(zf):
            all_globals |= set(globals_in_pickle(zf.read(member)))

    needs_action = sorted(g for g in all_globals if g not in builtin)
    already = sorted(g for g in all_globals if g in builtin)

    print(f"\n# === ALL globals referenced by {path} ===")
    for mod, nm in sorted(all_globals):
        print(f"#   {mod}.{nm}")
    print(f"\n# === already permitted by torch weights_only ({len(already)}) ===")
    for mod, nm in already:
        print(f"#   {mod}.{nm}")
    print(f"\n# === MUST be audited + allowlisted ({len(needs_action)}) ===")
    for mod, nm in needs_action:
        print(f"#   {mod}.{nm}")
    if any(m is None or n is None for m, n in needs_action):
        print("# !! some operands could not be resolved statically -> FAIL LOUD, "
              "inspect manually; do NOT load.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
