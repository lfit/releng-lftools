#!/bin/bash

if [ $# -ne 2 ]; then
    echo 1>&2 "Usage: $0 FILE PROJECTCODE"
    exit 1
fi

readarray -t repos < "$1"
prefix=$2
for line in "${repos[@]}"
do
    repo=$(echo "${line}" | cut -f1)
    echo "${repo}"
    hyph=$(echo "${repo}" | tr / -)
    printf "\thyphenated: %s\n" "${hyph}"
    group="${prefix}-gerrit-${hyph}-committers"
    printf "\tgroup: %s\n" "${group}"
    lftools lfidapi create_group "${group}"
done
echo 'done'
