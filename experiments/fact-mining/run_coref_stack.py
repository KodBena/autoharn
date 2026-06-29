#!/usr/bin/env python
"""run_coref_stack.py — bring up BOTH host coref daemons as one supervised process.

The coref stack is two daemons by the host-XOR-device split (ADR-0012 P9): the JAX
unified coref daemon (encode+decode, :5600) and the torch/spaCy nlp_server (parse +
the --coref-verify reference, :5599). Running them by hand is two terminals + a
start-order gotcha (nlp_server's warmup relays to the decode daemon). This wrapper
removes that friction:

  * starts the DECODE daemon first and waits until it answers a ping (so nlp_server's
    warmup never relays into a not-yet-listening socket),
  * then starts nlp_server pointed at it (--coref-backend jax-unified --decode-addr ...),
  * prefixes both daemons' output ([decode]/[nlp]) onto this one console,
  * on ^C (or if either daemon dies) tears BOTH down cleanly, in order.

The children run in their OWN session (start_new_session=True), so ^C hits only this
supervisor — it then signals the children, rather than the terminal SIGINT-ing all
three at once in an uncontrolled order.

After it's up, the client needs ONE url (--decode-addr is optional; nlp_server uses the
one set here):

    python load_facts.py <text> --remote tcp://<host>:5599 --coref --coref-backend jax-unified

Run (host, in this dir):
    python run_coref_stack.py --deberta-weights ./fixtures/deberta_maverick.npz \
        --weights ./fixtures/weights.npz --model en_core_web_trf --gpu
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def _pump(proc: subprocess.Popen, prefix: str) -> None:
    """Forward a child's merged stdout/stderr to our console, line-prefixed."""
    assert proc.stdout is not None
    for raw in iter(proc.stdout.readline, b""):
        sys.stdout.buffer.write(f"[{prefix}] ".encode() + raw)
        sys.stdout.buffer.flush()


def _wait_ready(addr: str, timeout_s: float, label: str) -> bool:
    """Ping a ZMQ REP daemon until it answers (it may be loading weights / cold-compiling)
    or timeout. Returns True once it ponged. Reconnects each attempt (a REQ socket with an
    unanswered send is wedged)."""
    import zmq

    ctx = zmq.Context.instance()
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        sock = ctx.socket(zmq.REQ)
        sock.setsockopt(zmq.LINGER, 0)
        sock.connect(addr)
        sock.send_json({"op": "ping"})
        if sock.poll(1500, zmq.POLLIN):
            sock.recv_multipart()
            sock.close(0)
            print(f"[stack] {label} ready at {addr}", flush=True)
            return True
        sock.close(0)
        time.sleep(0.5)
    return False


def _spawn(argv: list[str], prefix: str, extra_env: dict | None = None) -> subprocess.Popen:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(
        argv, cwd=HERE, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True,  # own process group: ^C reaches only the supervisor
    )
    threading.Thread(target=_pump, args=(proc, prefix), daemon=True).start()
    return proc


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host-ip", default="192.168.122.1",
                    help="IP the client reaches the daemons on (the relay/decode addrs "
                         "nlp_server hands out use it). default %(default)s")
    ap.add_argument("--nlp-port", type=int, default=5599)
    ap.add_argument("--decode-port", type=int, default=5600)
    ap.add_argument("--weights", default="./fixtures/weights.npz",
                    help="decode-tail weights .npz")
    ap.add_argument("--deberta-weights", default="./fixtures/deberta_maverick.npz",
                    help="fine-tuned deberta encoder .npz (its .spm sibling is vendored alongside)")
    ap.add_argument("--model", default="en_core_web_trf", help="nlp_server parse model")
    ap.add_argument("--gpu", action="store_true", help="run nlp_server on the GPU")
    ap.add_argument("--mem-fraction", default="0.3",
                    help="XLA_PYTHON_CLIENT_MEM_FRACTION for the decode daemon (share the card "
                         "with the torch nlp_server). default %(default)s")
    ap.add_argument("--ready-timeout", type=float, default=300.0,
                    help="seconds to wait for the decode daemon to answer a ping (cold compile "
                         "can be slow the first time). default %(default)s")
    a = ap.parse_args()

    decode_bind = f"tcp://0.0.0.0:{a.decode_port}"
    decode_addr = f"tcp://{a.host_ip}:{a.decode_port}"  # the addr nlp_server relays to
    nlp_bind = f"tcp://0.0.0.0:{a.nlp_port}"

    procs: list[tuple[str, subprocess.Popen]] = []
    try:
        # (1) decode daemon FIRST, so nlp_server's warmup can reach it.
        decode = _spawn(
            [sys.executable, "coref_decode_server.py", "--addr", decode_bind,
             "--weights", a.weights, "--deberta-weights", a.deberta_weights],
            "decode", extra_env={"XLA_PYTHON_CLIENT_MEM_FRACTION": a.mem_fraction})
        procs.append(("decode", decode))
        if not _wait_ready(decode_addr, a.ready_timeout, "decode daemon"):
            raise SystemExit("[stack] decode daemon did not become ready; aborting")

        # (2) nlp_server, pointed at the decode daemon, jax-unified by default.
        nlp_argv = [sys.executable, "nlp_server.py", "--addr", nlp_bind,
                    "--model", a.model, "--coref-backend", "jax-unified",
                    "--decode-addr", decode_addr]
        if a.gpu:
            nlp_argv.append("--gpu")
        nlp = _spawn(nlp_argv, "nlp")
        procs.append(("nlp", nlp))

        print(f"[stack] both daemons up. Client needs ONE url:\n"
              f"        python load_facts.py <text> --remote tcp://{a.host_ip}:{a.nlp_port} "
              f"--coref --coref-backend jax-unified\n"
              f"[stack] ^C to stop both.", flush=True)

        # supervise: exit if EITHER daemon dies (a dead half is a broken stack).
        while True:
            for name, p in procs:
                rc = p.poll()
                if rc is not None:
                    raise SystemExit(f"[stack] {name} daemon exited (code {rc}); shutting down")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[stack] ^C — stopping both daemons", flush=True)
    finally:
        # stop nlp first (it depends on decode), then decode; SIGINT, then escalate.
        for name, p in reversed(procs):
            if p.poll() is None:
                try:
                    p.send_signal(signal.SIGINT)
                except ProcessLookupError:
                    pass
        for name, p in reversed(procs):
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"[stack] {name} did not stop on SIGINT; killing", flush=True)
                p.kill()
        print("[stack] stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
