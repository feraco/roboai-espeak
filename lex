#!/bin/bash
# Lex Channel Chief CLI launcher following OM1 patterns
cd "$(dirname "$0")"
exec uv run python src/control/lex_cli.py "$@"
