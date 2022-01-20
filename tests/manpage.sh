#!/bin/bash

# Preview and convert MD file to manpage.
# Ref:
#   https://www.howtogeek.com/682871/how-to-create-a-man-page-on-linux/

tests_dir=$(realpath $(dirname "${0}"))
root_dir=$(dirname "$tests_dir")
app_name=$(basename "$root_dir")
draft="${root_dir}/data/man/${app_name}.1.md"
outfile="${draft%.*}"
outfile="${outfile##*/}"
outfile="${root_dir}/debian/${outfile}"
if [[ -z "$1" || "$1" == 'preview' || "$1" == 'p' ]]; then
    pandoc "$draft" -s -t man | man -l -
elif [[ "$1" == 'convert' || "$1" == 'c' ]]; then
    pandoc "$draft" -s -t man -o "$outfile"
fi
