#!/bin/bash
set -o errexit
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sanity_checks () {

echo "sandbox mode=$sandbox"
echo gerrit url="$project"
echo new repo name ="$repository"
echo INFOFILE="$(pwd)/$info_file"
echo LICENSE="$(pwd)/$license_file"
echo "Gerrit Create Project:"
echo "ssh -p 29418 "$user"@"$project" "gerrit create-project $repository --empty-commit --parent All-Projects""

read -p "Press any key to continue"

TMP_WORKSPACE="${OPTARG:-/tmp/}"

if ! [[ -z "$info_file" ]]; then
  INFOFILE="$(pwd)/$info_file"
  echo "Linting $info_file"
  set -e errexit
  yamllint "$info_file"
  set +e errexit
fi

if ! [[ -z "$license_file" ]]; then
  LICENSE="$(pwd)/LICENSE"
fi


if [[ -z "$repository" ]]; then
  echo "repository name not defined"
  exit 1
fi

if [[ $(ssh -p 29418 "$user"@"$project" gerrit version) ]];
then
  echo "can connect to gerrit"
else
  echo "cannot connect to gerrit"
  exit 1
fi

#Exit if project already exists
  set -e errexit
ssh -p 29418 "$user"@"$project" gerrit  set-project "$repository"  &> /dev/null && \
echo "$repository Already exists, cannot create exiting" && exit 1
  set +e errexit

}

movetoworkspace () {
if ! [[ -d "$TMP_WORKSPACE" ]]; then
  echo $TMP_WORKSPACE
  mkdir -p "$TMP_WORKSPACE"
fi
cd $TMP_WORKSPACE
}

create_and_clone_repo () {
echo "Creating repository $repository"
ssh -p 29418 "$user"@"$project" "gerrit create-project $repository --empty-commit --parent All-Projects"

movetoworkspace "$@"

if ! [[ -d "$repository" ]];
then
  git clone ssh://"$user"@"$project":29418/"$repository" "$repository" &> /dev/null
  cd "$repository"
  git fetch origin refs/meta/config &> /dev/null && git checkout FETCH_HEAD &> /dev/null
fi

# Sandbox mode
sandboxmode "$@"

}

create_groups_file () {

groupsfile="$DIR/$shortname/Create_Groups_file"

if [ -f "$groupsfile" ]; then
  cd "$TMP_WORKSPACE"/"$repository"
  echo "############# GROUPS FILE #################"
  source "$groupsfile" "$@"
  echo ""

  git add groups
  git commit -sv -m "Creating groups file"  &> /dev/null

  if git push origin HEAD:refs/meta/config &> /dev/null; then
    echo "git push for groups file succeeded"
  else
    echo "git push for groups file failed"
    exit 1
  fi
fi

}

create_repository_config () {

repofile="$DIR/$shortname/Create_Repository_config"

if [ -f "$repofile" ]; then
echo "####### adding $repository project.config access refs meta config ##########"
  cd "$TMP_WORKSPACE"/"$repository"
  source "$repofile" "$@"
  cat project.config

  git add project.config
  git commit -sv -m "Pushing $repository project.config to refs/meta/config"

  if git push origin HEAD:refs/meta/config &> /dev/null; then
    echo "git push for $repository refs meta config succeeded"
  else
    echo "git push for $repository refs meta config succeeded"
    exit 1
  fi
fi

}

gitreviewandlicense () {

git reset --hard origin/master &> /dev/null

# Sandbox mode
sandboxmode "$@"

#user=sanbox\n\
cp "$LICENSE" .
printf "[gerrit]\n\
host="$project"\n\
port=29418\n\
project=$repository.git\n" > .gitreview
git add LICENSE .gitreview
git commit -sv -m "Forcing .gitreview and LICENSE into repo"
git push ssh://$user@$project:29418/$repository HEAD:refs/heads/master &> /dev/null
git fetch &> /dev/null && git merge &> /dev/null
echo ""

#Make info file optional
if [[ -f "$INFOFILE" ]]; then
  echo "############# Adding info file for review ####################"
  cp "$INFOFILE" .
  git add "$info_file"
  git commit -sv -m "Adding $info_file for review"
  git review

fi
}

allprojects () {
#Only runs if project needs additional permissions in All_Projects

allprojectsfile="$DIR/$shortname/Create_All_Projects_config"
if [ -f "$allprojectsfile" ]; then
echo ""
echo "####### updating $repository project.config for All-projects ##########"
movetoworkspace "$@"
git clone ssh://"$user"@"$project":29418/All-Projects All-Projects-"$repository" &> /dev/null
cd "$TMP_WORKSPACE"/All-Projects-"$repository"

sandboxmode "$@"

source "$allprojectsfile" "$@"

git add project.config
if git push origin HEAD:refs/meta/config &> /dev/null; then
  echo "git push for All-projects project.config file succeeded"
else
  echo "git push for All-projects project.config file failed "
  exit 1
fi

fi

}

sandboxmode() {
if  [[ $sandbox = "true" ]]; then
  git config gitreview.username "sandbox"
  git config user.name "sandbox"
  git config user.email "sandbox@example.org"
fi
}

usage() {
cat << EOF
"$0": Creates a repository and sets up the permissions.

usage: $0 [OPTIONS]
 -h  Show this message
 -p  project url eg: gerrit.localhost
 -n  project short name: eg: opnfv odl onap
 -r  repository name
 -u  ssh user name
 -w  workspace to do clones etc. (must not be in a git repo)
     Default is /tmp/
 -i  INFO.yaml file
 -l  LICENSE file
 -s  Sandbox mode eg:
     git config gitreview.username "sandbox"
     git config user.email "sandbox@example.org"


example: $0  -p gerrit.localhost -n opnfv -r reponame -u sandbox -i INFO.yaml -l LICENSE

EOF

exit 1

}

if [[ -z "$@" ]]; then usage
fi

while getopts "p:n:r:i:l:u:w:sh" OPTION
do
        case $OPTION in
                p ) project="$OPTARG" ;;
                n ) shortname="$OPTARG" ;;
                r ) repository="$OPTARG" ;;
                i ) info_file="$OPTARG" ;;
                l ) license_file="$OPTARG" ;;
                u ) user="$OPTARG" ;;
                w ) TMP_WORKSPACE="$OPTARG" ;;
                s ) sandbox="true" ;;
                h ) usage; exit;;
                \? ) echo "Unknown option: -$OPTARG" >&2; exit 1;;
        esac
done

sanity_checks "$@"
create_and_clone_repo "$@"
create_groups_file "$@"
create_repository_config "$@"
gitreviewandlicense
allprojects "$@"

echo "Repo Configured"
echo gerrit url="$project"
echo project="$project"
echo repository="$repository"

