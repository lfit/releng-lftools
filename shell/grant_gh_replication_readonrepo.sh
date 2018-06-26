#!/bin/bash
set -o errexit
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sanity_checks () {
TMP_WORKSPACE="${OPTARG:-/tmp/}" 

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
}

movetoworkspace () {
if ! [[ -d "$TMP_WORKSPACE" ]]; then
  echo $TMP_WORKSPACE
  mkdir -p "$TMP_WORKSPACE"
fi
cd $TMP_WORKSPACE
}

create_and_clone_repo () {

movetoworkspace "$@"

if ! [[ -d "$repository" ]];
then
  git clone ssh://"$user"@"$project":29418/"$repository" "$repository" &> /dev/null
  cd "$repository"
  git fetch origin refs/meta/config &> /dev/null && git checkout FETCH_HEAD &> /dev/null
fi

}

create_groups_file () {

#Groups File OPNFV
cd "$TMP_WORKSPACE"/"$repository"

#get uuid for Non-Interactive and GitHub users into groups file

if egrep '(GitHub)' groups; then 
  echo "Github already in groups"
  exit 1
  
fi


ssh -p 29418 "$user"@"$project" gerrit ls-groups --verbose \
    | egrep 'GitHub'\
      | awk '{print $3"\t"$1,$2}' > groups.tmp


cat groups.tmp groups > addedgroups
mv addedgroups groups
rm groups.tmp

git add groups
git commit -sv -m "Creating groups file"

if git push origin HEAD:refs/meta/config;  then
  echo "git push for groups file succeeded"
else
  echo "git push for groups file failed"
  exit 1
fi

}

grant_gh_read_on_refs () {
cd "$TMP_WORKSPACE"/"$repository"

git config  --add -f project.config 'access.refs/*.read' "group Github Replication"

git add project.config
git commit -sv -m "Pushing $repository project.config to refs/meta/config"
  
if git push origin HEAD:refs/meta/config; then
  echo "git push for $repository refs meta config succeeded"
else
  echo "git push for $repository refs meta config FAILED"
  exit 1
fi
      
}

usage() {
cat << EOF
"$0": Creates a repository and sets up the permissions.

usage: $0 [OPTIONS]
 -h  Show this message
 -p  project url eg: gerrit.localhost
 -r  repository name
 -u  ssh user name
 -w  workspace to do clones etc. (must not be in a git repo)
     Default is /tmp/

example: $0  -p gerrit.localhost -r reponame -u username

EOF

exit 1

}

if [[ -z "$@" ]]; then usage
fi

while getopts "p:r:u:w:h" OPTION
do
        case $OPTION in
                p ) project="$OPTARG" ;;
                r ) repository="$OPTARG" ;;
                u ) user="$OPTARG" ;;
                w ) TMP_WORKSPACE="$OPTARG" ;;
                h ) usage; exit;;
                \? ) echo "Unknown option: -$OPTARG" >&2; exit 1;;
        esac
done

sanity_checks "$@"
create_and_clone_repo "$@"
create_groups_file "$@"
grant_gh_read_on_refs "$@"

