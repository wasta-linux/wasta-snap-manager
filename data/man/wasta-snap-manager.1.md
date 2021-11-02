% Wasta [Snap] Manager
% Nate Marti
% November 2021

# NAME
wasta-snap-manager - selectively manage snap packages offline or online

# SYNOPSIS
**wasta-snap-manager** [OPTION...] [SNAP...]

# DESCRIPTION
Install or update snap packages from a wasta-offline device or any other arbitrary
folder. Elevated privileges are required, e.g.:
pkexec wasta-snap-manager
sudo wasta-snap-manager

# OPTIONS
**-h**, **--help**
: Show help.

**-d**, **--debug**
: Set log level to DEBUG.

**-i**, **--online**
: Update snaps from the online Snap Store.

**-s**, **--snaps-dir=/path/to/wasta-offline**
: Update snaps from offline folder.

**-V**, **--version**
: Print wasta-snap-manager and snapd version numbers.

# EXAMPLES
**wasta-snap-manager**
: Launch the app in a window.

**wasta-snap-manager -s /media/user/USB-64GB/wasta-offline**  
: Update all updatable snap packages from the wasta-offline folder.

**wasta-snap-manager -s /home/user/snaps-archive**  
: Update all updatable snap packages from the given folder.

**wasta-snap-manager -i -s /media/user/USB-64GB/wasta-offline**  
: Update first from the offline folder, then from the Snap Store.

**wasta-snap-manager -s /media/user/USB-64GB/wasta-offline firefox thunderbird**  
: Install or update the listed snap packages from the offline folder.

# BUGS
Bug reports can be found and filed at https://github.com/wasta-linux/wasta-snap-manager/issues
