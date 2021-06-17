#!/bin/sh

site="github.com"
oldBranch="master"
newBranch="main"
bin="gh" # or set to 'hub'
user="${1:-""}"
repo="${2:-""}"

# Funtion to get repository details
askRepo() {
	# return if repo is already set (passed as arg)
	test ! -z "$repo" && return

	url="$(git config --get remote.origin.url)"
	repo="$(basename -s .git "$url")"

	printInfo "github repository name (default: %s): " "$repo"
	read -r

	# trim whitespace
	REPLY="$(echo "$REPLY" | xargs)"

	repo="${REPLY:-$repo}"
	printInfo "input: $repo\n\n"
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
git push origin "$oldBranch"

if ! localMainExists; then
	printInfo "renaming '$oldBranch' to '$newBranch' locally\n"
	git checkout $oldBranch
	git branch --move $oldBranch "$newBranch"
fi

# ensure 'main' is at remote
if ! remoteMainExists; then
	printInfo "setting '$newBranch' as default upstream branch\n"
	git checkout "$newBranch"
	git push --set-upstream origin "$newBranch"
fi

# remove local 'master' branch
if localMasterExists; then
	printInfo "renaming local $oldBranch branch\n"
	git branch --delete $oldBranch
fi

# remove remote 'master' branch
if remoteMasterExists; then
	printInfo "deleting remote $oldBranch branch\n"

	# if this fails, it may be due to forgetting
	# to reset the default branch to 'main' on github
	git push origin --delete $oldBranch

	test ! $? && printInfo "this probably errored since '$oldBranch' is still the 'default branch' on github" \
		&& printInfo "if you install \`gh\` and \`jq\` this will be done for you"
fi
