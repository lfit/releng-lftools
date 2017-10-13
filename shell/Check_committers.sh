#!/bin/bash
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2016, 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

main() {

echo "checking $GERRIT with $FILE with first line:"
head -n1 "$FILE"
echo ""

while read -r line; do

  email="$(echo "$line" | awk '{print $NF}')"
  group="$(echo "$line" | awk '{print $1}')"
  fullname="$(echo "$line" | awk '{print $2, $3}')"
  sixmonthsago=$(date -d "-6 month" +%Y-%m-%d)
  # Check if user can be found in gerrit in the last six months
  change_id="$(curl --silent "https://$GERRIT/r/changes/?q=""$email"+after:"$sixmonthsago""&n=1" | grep change_id)";


  if  [[ -z $change_id ]]; then

  # Check if user can be found in gerrit at all
  change_id="$(curl --silent "https://$GERRIT/r/changes/?q=$email&n=1" | grep change_id)";

    if  ! [[ -z $change_id ]]; then
      printf '%s\n' "$group \"$fullname\" has not used gerrit in _6_ months $email"
    else
      printf '%s\n' "$group \"$fullname\" has ______never______ used gerrit $email"
    fi

  fi

done < <(cat "$FILE" )

}

usage() {
cat << EOF
This program searches gerrit by email for user participation
Email list can be built with 'ldap-lookup'
Program outputs users who have not used gerrit at all, or in the last 6 months
users from this list can be slated to have their access revoked.

Note you will need: TLS_REQCERT never in your ldap.conf for 
3rdparty/ldap-lookup to work.

Usage:
 -g  target gerrit url
 -f  target list file

Build List:
python ldap-lookup group_name(s) > file
ex ./ldap-lookup opnfv-gerrit*  > all_opnfv_ldap

Trigger gerrit search from list:
ex: $0 -g gerrit.opnfv.org -f all_opnfv_ldap
EOF
}


if [[ -z "$@" ]]; then usage
  exit 1
fi

while getopts "g:f:h" OPTION
do
        case $OPTION in
                g ) GERRIT="$OPTARG";;
                f ) FILE="$OPTARG" ;;
                h ) usage; exit;;
                \? ) echo "Unknown option: -$OPTARG" >&2; exit 1;;
        esac
done

main "$@"

