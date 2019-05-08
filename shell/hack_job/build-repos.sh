#!/bin/bash

if [ $# -ne 3 ]; then
    echo 1>&2 "Usage: $0 FILE PROJECTCODE GERRIT"
    exit 1
fi

readarray -t repos < "$1"
prefix=$2
server=$3

declare -A created
for line in "${repos[@]}"
do
    repo=$(echo "${line}" | cut -f1)
    if ! [ "${created[$repo]}" ]
    then
        echo "creating ${repo}"
        hyph=$(echo "${repo}" | tr / -)
        printf "\t%s\n" "$hyph"
        # shellcheck disable=SC2029
        ssh "${server}" "gerrit create-project ${repo} --empty-commit -o ldap/${prefix}-gerrit-${hyph}-committers"
        created[${repo}]=1
    else
        echo "${repo} already created, skipping"
    fi
done
echo 'done'
