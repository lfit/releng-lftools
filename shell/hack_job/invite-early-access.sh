#!/bin/bash
readarray -t earlyaccess < early-access.txt
for email in "${earlyaccess[@]}"
do
    echo "${email}"
    lftools lfidapi invite "${email}" oran-early-access
#    hyph=$(echo "${repo}" | tr / -)
#    printf "\t%s\n" "$hyph"
#    ssh gerrit.oran-osc.org "gerrit create-project ${repo} --empty-commit -o ldap/oran-gerrit-${hyph}"
#    echo 'done'
done
#while read -r repo
#do
#    echo "${repo}"
#    hyph=$(echo "${repo}" | tr / -)
#    printf "\t%s\n" "$hyph"
#    $(ssh gerrit.oran-osc.org "gerrit create-project ${repo} --empty-commit -o ldap/oran-gerrit-${hyph}")
#    echo 'done'
#done < repos.txt
