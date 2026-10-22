#!/usr/bin/env bash
# Compatibility entry point for the submitted evaluation.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 -B evals/reproduce.py
