#!/bin/sh
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# COPYRIGHT
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

site=$1
oldBranch=$2
newBranch=$3
repo="${4:-""}"
# Funtion to get repository details
askRepo() {
	# return if repo is already set (passed as arg)
	test ! -z "$repo" && return
	url="$(git config --get remote.origin.url)"
	repo="$(basename -s .git "$url")"
	 echo "github repository name (default: %s): " "$repo"
	read -r REPLY
	# trim whitespace
	REPLY="$(echo "$REPLY" | xargs)"
	repo="${REPLY:-$repo}"
	echo "input: $repo\n\n"
}
# Funtion to check existance of remote Main details
remoteMainExists() {
	git show-branch "refs/remotes/origin/$newBranch" >/dev/null 2>&1
}
# Funtion to check existance of remote Master details
remoteMasterExists() {
	git show-branch "refs/remotes/origin/$oldBranch" >/dev/null 2>&1
}
# Funtion to check existance of local Main details
localMainExists() {
	git rev-parse --verify --quiet "refs/heads/$newBranch" >/dev/null
}
# Funtion to check existance of local Master details
localMasterExists() {
	git rev-parse --verify --quiet "refs/heads/$oldBranch" >/dev/null
}
git fetch --all
git checkout "$oldBranch"
if ! localMainExists; then
	echo "renaming '$oldBranch' to '$newBranch' locally\n"
	git checkout $oldBranch
	git branch --move $oldBranch "$newBranch"
fi
# ensure 'main' is at remote
if ! remoteMainExists; then
	echo "setting '$newBranch' as default upstream branch\n"
	git checkout "$newBranch"
	git push --set-upstream origin "$newBranch"
fi
# remove local 'master' branch
if localMasterExists; then
	echo "renaming local $oldBranch branch\n"
	git branch --delete $oldBranch
fi
# remove remote 'master' branch
if remoteMasterExists; then
	echo "deleting remote $oldBranch branch\n"
	# if this fails, it may be due to forgetting
	# to reset the default branch to 'main' on github
	git push origin --delete $oldBranch
	test ! $? && echo "this probably errored since '$oldBranch' is still the 'default branch' on github" \
		&& echo "if you install \`gh\` and \`jq\` this will be done for you"
fi
