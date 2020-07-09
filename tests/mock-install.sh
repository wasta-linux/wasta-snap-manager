#!/bin/bash

### This script "installs" the polkit authentication and binary files in order
### to test the app in development.

# This script needs sudo privileges.
# ---------------------------------------------------------------------------
if [[ $(id -u) -ne 0 && ! $1 == '-h' ]]; then
    echo "This script needs to be run with root privileges. Exiting."
    exit 1
fi

BASE=$(realpath $(dirname $0))
BIN=/usr/bin
POLKIT=/usr/share/polkit-1/actions

bins=(
    snap-settings
)

actions=(
    org.wasta.apps.snap-settings.policy
)

if [[ ! $1 ]]; then
    # Create symlinks for binaries.
    for b in ${bins[@]}; do
        if [[ ! -e $BIN/$b ]]; then
            cp -s "$BASE/../src/$b" "$BIN"
            echo "$BASE/../src/$b -> $BIN"
        fi
    done

    # Create symlinks for polkit files.
    for a in ${actions[@]}; do
        if [[ ! -e $POLKIT/$a ]]; then
            cp -s "$BASE/../$a" "$POLKIT"
            echo "$BASE/../$a -> $POLKIT"
        fi
    done

elif [[ $1 == '-d' ]]; then
    # Remove symlinks for binaries.
    for b in ${bins[@]}; do
        if [[ -L $BIN/$b ]]; then
            rm "$BIN/$b"
            echo "symlink at $BIN/$b removed"
        fi
    done

    # Remove symlinks for polkit files.
    for a in ${actions[@]}; do
        if [[ -L $POLKIT/$a ]]; then
            rm "$POLKIT/$a"
            echo "symlink at $POLKIT/$a removed"
        fi
    done
fi

exit 0
