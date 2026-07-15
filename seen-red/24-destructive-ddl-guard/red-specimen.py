# SEEN-RED specimen for the destructive-ddl-guard (finding 24/30). An UNDECLARED executable CASCADE —
# exactly the shape that took out acts.ruling as collateral. The guard MUST flag this (never silent).
import subprocess
subprocess.run(["psql", "-d", "harness", "-c", "DROP SCHEMA acts CASCADE"])
