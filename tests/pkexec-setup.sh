#!/bin/bash

# Install or remove pkexec policy file for running app from repo.

# Get repo's home folder path; assumes script is in $repo_home/tests.
parent_dir=$(dirname $(realpath "$0"))
repo_dir=$(dirname "$parent_dir")
bin_path="${repo_dir}/bin/wasta-snap-manager"

policy_name="org.wasta.apps.test-wasta-snap-manager.policy"
policy_file="${parent_dir}/${policy_name}"
# Edit policy_file for current repo.
# ln -s "$policy_file" "~/${policy_name}"
policies_dir='/usr/share/polkit-1/actions'
if [[ "$1" == 'install' ]]; then
    sudo cp -l "$policy_file" "$policies_dir"
elif [[ "$1" == 'uninstall' ]]; then
    sudo rm "${policies_dir}/${policy_name}"
else
    echo "Pass 'install' or 'uninstall' as 1st arg."
    exit 1
fi
