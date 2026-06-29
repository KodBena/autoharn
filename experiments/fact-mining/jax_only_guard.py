#!/usr/bin/env python
"""Make the unified JAX coref daemon STRUCTURALLY torch-free (ADR-0012 device hygiene).

THE HEADLINE. This whole workflow exists to ELIMINATE the torch/jax coexistence, not
relocate it. The unified daemon must run the WHOLE coref forward — tokenize+mask
(spaCy + HF tokenizer) -> jax_deberta.encode -> jax decode — in ONE process that
imports jax and NEVER torch. The trap (verified on the guest, 2026-06-29): two of the
daemon's torch-free-LOOKING dependencies drag torch in transitively —

  * `from transformers import AutoTokenizer` imports torch at module load (the fast
    deberta tokenizer is framework-agnostic, but `transformers`'s package __init__
    eagerly imports the torch integration unless USE_TORCH=0);
  * `import spacy` autoloads its registered entry-point plugins, and the installed
    `spacy_curated_transformers` / `spacy_transformers` factories HARD-import torch
    (no try/except) the moment spaCy enumerates `registry._entry_point_factories`.

Either one silently re-introduces torch into the jax-only process — the exact
"coexistence relocated, not eliminated" failure ADR-0012 P9 / the host-XOR-device
discipline forbids. The import-XOR AST gate (test_import_xor.py) CANNOT catch this: it
scans OUR files' import statements, and `transformers`/`spacy` are neither host nor
device tokens, so a torch import reached THROUGH them is invisible to a static scan.
The mechanism therefore has to be a RUN-TIME one (ADR-0011 Rule 1: the strongest
feasible surface for a failure a static gate cannot see).

THE MECHANISM (`install()`), set up ONCE before any of transformers/spacy/jax import.
A single `MetaPathFinder` at the FRONT of sys.meta_path, plus the framework env flags:

  1. `os.environ["USE_TORCH"]="0"` (+ USE_TF/USE_FLAX) — tells transformers to skip its
     torch integration at import; the fast tokenizer still loads (pure `tokenizers`-lib),
     and transformers then never probes torch, so the finder below need not satisfy a
     torch availability check.
  2. the finder BLOCKS `torch`: `import torch` (or any `torch.*`) hits a loader whose
     `create_module` RAISES `ModuleNotFoundError` — fail-loud (ADR-0002), and crucially
     the failed import is NOT cached, so `sys.modules` keeps NO `torch` key. That last
     point is why we do NOT use the `sys.modules["torch"]=None` poison: a `None` entry
     makes `getattr(sys.modules["torch"], "Tensor")` raise `AttributeError`, which
     scipy's `array_api_compat.is_torch_array` (reached through spaCy's deps) does
     unconditionally — the absent-key form it tolerates (its lookup is `try: sys.modules
     [name] except KeyError: return False`). Blocking-not-poisoning makes "no torch"
     UNREPRESENTABLE (`import torch` cannot succeed) AND scipy-tolerant.
  3. the SAME finder serves a harmless DUMMY module for the torch-dragging spaCy trf
     plugins (`spacy_curated_transformers`, `spacy_transformers`, `curated_transformers`).
     spaCy's `registry._entry_point_factories.get_all()` imports each registered plugin
     for its registration side-effect; the dummy lets that succeed (registering nothing
     we use — we use only the rule-based en_core_web_sm TOKENIZER, no trf component)
     WITHOUT the plugin's unguarded `import torch` ever running.

`assert_torch_free()` is the FAIL-LOUD backstop (ADR-0002): after the daemon has
imported everything, it asserts torch never materialised (`sys.modules` has no real
`torch`) — so if a future dependency finds a new path to torch BEFORE the guard, or one
the finder does not cover, the daemon dies loudly at startup instead of silently running
a torch+jax process. The whole point, made checkable.

This module imports only stdlib (sys/os/types/importlib): it is host-XOR-device
TRIVIALLY (neither side), safe to import anywhere, and is scanned by both gates to
prove it authors no host array lib and no device op.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import os
import sys
import types

# The torch-dragging spaCy trf plugins. We use ONLY en_core_web_sm's rule-based
# tokenizer (word split + char offsets), never a transformer component, so stubbing
# these out costs nothing — and stops their unguarded `import torch` at the source.
_BLOCKED_PLUGIN_PREFIXES = (
    "spacy_curated_transformers",
    "spacy_transformers",
    "curated_transformers",
)


class _DummyAttr:
    """Returns itself for any attribute/call so a stubbed plugin module can be
    imported AND have arbitrary `module:object` entry-point targets resolved without
    executing the real (torch-importing) code. We never invoke these — spaCy only
    imports the plugin for its registration side-effect, which the dummy no-ops."""

    def __call__(self, *a, **k):
        return _DummyAttr()

    def __getattr__(self, name):
        return _DummyAttr()


class _StubLoader(importlib.abc.Loader):
    def create_module(self, spec):
        m = types.ModuleType(spec.name)
        m.__path__ = []  # mark as a package so submodule imports route back through us
        m.__getattr__ = lambda name: _DummyAttr()  # any attr / submodule object -> dummy
        return m

    def exec_module(self, module):
        pass


class _BlockLoader(importlib.abc.Loader):
    """Makes an import FAIL (and stay uncached). `create_module` raising means the
    import never completes, so `sys.modules` gets NO entry — the absent-key form
    scipy/array_api_compat tolerate, unlike a `None` poison."""

    def create_module(self, spec):
        raise ModuleNotFoundError(
            f"'{spec.name}' is disabled in the jax-only coref daemon (jax_only_guard): "
            "this process must import jax and NEVER torch (ADR-0012 host-XOR-device).")

    def exec_module(self, module):  # pragma: no cover - create_module already raised
        pass


class _TorchFreeFinder(importlib.abc.MetaPathFinder):
    """At the front of sys.meta_path: BLOCKS torch (raising loader -> import fails,
    uncached) and STUBS the torch-dragging spaCy trf plugins (dummy module -> their
    unguarded `import torch` never runs). Nothing else is intercepted."""

    def find_spec(self, name, path=None, target=None):
        top = name.split(".")[0]
        if top == "torch":
            return importlib.machinery.ModuleSpec(name, _BlockLoader())
        if top in _BLOCKED_PLUGIN_PREFIXES:
            return importlib.machinery.ModuleSpec(name, _StubLoader(), is_package=True)
        return None


_INSTALLED = False


def install() -> None:
    """Make this process torch-free, idempotently. MUST be called before importing
    transformers / spaCy (and harmless before jax). Safe to call more than once."""
    global _INSTALLED
    if _INSTALLED:
        return
    # (1) tell transformers to skip the torch (and TF/Flax) integration at import.
    os.environ.setdefault("USE_TORCH", "0")
    os.environ.setdefault("USE_TF", "0")
    os.environ.setdefault("USE_FLAX", "0")
    # (2) install the finder: blocks torch (raising loader, uncached) + stubs the
    #     torch-dragging spaCy trf plugins. If torch is ALREADY a real module (imported
    #     before the guard), we do NOT mask it — assert_torch_free() must fail loud.
    if not any(isinstance(f, _TorchFreeFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _TorchFreeFinder())
    _INSTALLED = True


def assert_torch_free() -> None:
    """FAIL LOUD (ADR-0002) if torch ever materialised in this process. The runtime
    backstop the static import-XOR gate cannot provide: a dependency that finds a path to
    torch dies here at startup, not silently as a torch+jax process. The finder keeps a
    blocked import UNCACHED, so a torch-free process has NO `torch` key in sys.modules;
    any real `torch` module object present means it was imported before the guard (or on
    a path the finder does not cover) — the coexistence this daemon exists to forbid."""
    mod = sys.modules.get("torch", None)
    if mod is not None:
        raise RuntimeError(
            "jax-only coref daemon is NOT torch-free: a real `torch` module is "
            "imported in this process. The unified daemon must import jax and NEVER "
            "torch (ADR-0012 host-XOR-device / device single-home). Call "
            "jax_only_guard.install() BEFORE importing transformers/spaCy, and check "
            "no dependency imported torch on a path the guard does not cover.")


if __name__ == "__main__":
    # This module is STDLIB-ONLY by design (host-XOR-device trivially), so its __main__
    # authors no spaCy/transformers/jax import — the end-to-end coexistence smoke proof
    # (spaCy + HF fast-tokenizer + jax loaded, torch blocked) lives in
    # test_torch_free_daemon.py, which IS a test and may import them.
    install()
    assert_torch_free()
    import sys as _sys
    _blocked = False
    try:
        import torch  # noqa: F401
    except ModuleNotFoundError:
        _blocked = True
    print("jax_only_guard installed; import torch blocked:", _blocked,
          "| torch in sys.modules:", "torch" in _sys.modules,
          "| finder active:",
          any(isinstance(f, _TorchFreeFinder) for f in _sys.meta_path))
