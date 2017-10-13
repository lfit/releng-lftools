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

while read -r line; do

  email="$(echo "$line" | awk -F"," '{print $NF}')"
  company=${email#*@}; company=${company%.*};
  fullname="$(echo "$line" | awk -F"," '{print $3}')"
  lfid="$(echo "$line" | awk -F"," '{print $2}')"

cat << EOF
    - name: '$fullname'
      email: '$email'
      company: '$company'
      uid: '$lfid'
      timezone: ''
EOF

#done < <(cat "$FILE" )
done < <(../3rdparty/ldap-lookup.py "$1")

}

usage() {
cat << EOF
Usage:

$0 ldap-group-name 

calls ../3rdparty/ldap-lookup.py "\$1" 
where \$1 is the ldap-group name you would like to build yaml for your INFO.yaml file

EOF
}

if [[ $# -eq 0 ]] ; then usage
  exit 1
fi

while getopts "f:h" OPTION
do
        case $OPTION in
                f ) FILE="$OPTARG" ;;
                h ) usage; exit;;
                \? ) echo "Unknown option: -$OPTARG" >&2; exit 1;;
        esac
done

main "$@"

