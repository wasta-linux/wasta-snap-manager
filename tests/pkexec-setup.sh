#!/bin/bash

# Install or remove pkexec policy file for running app from repo.

# Get repo's home folder path; assumes script is in $repo_home/tests.
parent_dir=$(dirname $(realpath "$0"))
repo_dir=$(dirname "$parent_dir")
bin_path="${repo_dir}/bin/wasta-snap-manager"

policy_name="org.wasta.apps.test-wasta-snap-manager.policy"
policy_file="${parent_dir}/${policy_name}"
policies_dir='/usr/share/polkit-1/actions'
if [[ "$1" == 'install' ]]; then
    # Edit policy_file for current repo.
    sudo cp "$policy_file" "$policies_dir"
    id=org.wasta.apps.test-wasta-snap-manager
    pathkey=org.freedesktop.policykit.exec.path
    # Get current path from XML file.
    current_bin_path=$(
        xmlstarlet select --template --match \
            "/policyconfig/action[@id='$id']/annotate[@key='$pathkey']" -n \
            "${policies_dir}/${policy_name}"
    )
    if [[ "$current_bin_path" != "$bin_path" ]]; then
        # Update path in XML file.
        sudo xmlstarlet edit --inplace --update \
            "/policyconfig/action[@id='$id']/annotate[@key='$pathkey']" -v "$bin_path" \
            "${policies_dir}/${policy_name}"
    fi
elif [[ "$1" == 'uninstall' ]]; then
    sudo rm "${policies_dir}/${policy_name}"
else
    echo "Pass 'install' or 'uninstall' as 1st arg."
    exit 1
fi
