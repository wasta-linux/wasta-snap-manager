#/bin/bash
# Testing communication with snapd socket.
snap="$1"
api_sock='/run/snapd.socket'
curl -XGET --unix-socket "$api_sock" "http://localhost/v2/snaps/$snap"
