#!/usr/bin/env bash
# Quality-gate hook entry point — the actual logic lives in harness_audit_rerun.py
exec python "$(dirname "$0")/harness_audit_rerun.py"
