#!/bin/bash
file_path=$(readlink -f "$0")
root_dir=$(dirname $(dirname "$file_path"))
cd "${root_dir}"

if [[ "$1" == '-v' ]] || [[ "$1" == '--verbose' ]]; then
    # Verbose output.
    python3 -m unittest discover -v -s tests/unit
    python3 -m unittest discover -v -s tests/integration
else
    # Simple output.
    python3 -m unittest discover -s tests/unit
    python3 -m unittest discover -s tests/integration
fi
