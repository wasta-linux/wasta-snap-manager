#!/bin/bash

pandoc ../data/man/wasta-snap-manager.1.md -s -t man | man -l -
