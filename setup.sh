#!/bin/bash

# Script base directory.
basedir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Local python modules.
lib_dir=$basedir/Lib
[[ "$PYTHONPATH" =~ "${lib_dir}" ]] || export PYTHONPATH=${lib_dir}:$PYTHONPATH
