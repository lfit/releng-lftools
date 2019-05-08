#!/bin/bash

if [ $# -ne 2 ]; then
    echo 1>&2 "Usage: $0 FILE PROJECTCODE"
    exit 1
fi

readarray -t committers < "$1"
prefix=$2
for line in "${committers[@]}"
do
    echo "${line}"
    repo=$(echo "${line}" | cut -f1)
    committer=$(echo "${line}" | cut -f2)
    printf "Repo: '%s'\n\t'%s'\n" "${repo}" "${committer}"
    hyph=$(echo "${repo}" | tr / -)
    printf "\t%s\n" "$hyph"
    lftools lfidapi invite "${committer}" "${prefix}-gerrit-${hyph}-committers"
done
echo 'done'
