"""impedance demo — the toy cross-library pipeline (the proof of type-sanity + ergonomics).

  * pipeline.py     — the MEDIATED pipeline (torch -> numpy/scipy -> jax), reads as a straight line
  * raw_pipeline.py — the RAW library-call mess (the before): the same math, hand-wired and unsafe
  * mismatches.py   — five deliberate impedances, each a mypy error at a library crossing
"""
