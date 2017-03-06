#!/usr/bin/env bash

# TODO: I want to be able to cover as many rules as possible http://yamllint.readthedocs.io/en/latest/rules.html
# This sctipt was taking care of the main problems to help me clear the errors faster
# TODO: yamllint throws new errors after old ones have been cleared
# I need to cycle through new errors until all are cleared (eventually)

function start_script {
 # Ask if processing all or just some files
 # TODO: Be able to let this script go by what it finds when running "yamllint ."
 echo 'Do you want to run this for all yaml files (1)'
 echo 'Or do you want to run this for one/some files (2)'

 read -r ALL_OR_SOME
 validate_initial_question "$ALL_OR_SOME"
}

function validate_initial_question {
 if [[ "$1" == 1 ]]; then
  echo 'Running yamllint for all yaml files ...'
  for FILE in `find . -name *yaml`; do
   echo "Processing $FILE ..."
   process_file "$FILE"
  done
  exit 1
 elif [[ "$1" == 2 ]]; then
  # TODO: Dont care if the input is full path or not
  echo 'Which files do you want to run yamllint for? (full path)'
  read -r FILES
  for FILE in $FILES; do
   echo "Processing $FILE ..."
   process_file "$FILE"
  done
  exit 1
 else
  echo 'The option provided is not valid ... let me ask again...'
  start_script
 fi
}

function loop_log_file {
 # loop through the file
 # If the line contains "error"
 # 1- Extract line number
 # 2- Extract expected
 # 3- Extract found
 # 4- Modify line by removing all spaces and add the expected spaces

 # TODO temp hack... fixing all lines that contain a project-name definition.
 # Handeling normally is failing for me... need to investigate further...
 #sed -i '/{project-name}/s/ */      /' $FILE

 while read l; do
  LINE=$l
  LINE_NUMBER=$( echo "$l" | cut -d ":" -f2 | cut -d ":" -f1 )
  if [[ $LINE == *error* ]] && [[ $LINE == *"wrong indentation"* ]]; then
   EXPECTED=$( echo "$l" | sed -e 's#.*expected \(\)#\1#' | sed 's/\s.*$//' )
   # FOUND might not be needed now, but maybe in future... leaving it there.
   # FOUND=$( echo "$l" | sed -e 's#.*found \(\)#\1#' | sed 's/\s.*$//' )
   # Remove all blanks from the beginning of the line
   sed -i "${LINE_NUMBER}s/^ *//g" "$FILE"
   # Making a loop to add "EXPECTED" spaces in the beginning of the line
   # this is just temporary meanwhile i figure something smarter
   # shellcheck disable=SC2034
   for space in $(seq 1 "$EXPECTED")
   do
    sed -i "${LINE_NUMBER}s/^/ /g" "$FILE"
   done
  elif [[ $LINE == *line-lenght* ]]; then
   # TODO There is not much the script can do, other than telling the user about it
   # Will think of something better to do here
   echo '==========LINE TOO LONG, FIX MANUALLY=========='
   echo "$LINE"
   echo '==============================================='
  elif [[ $LINE == *new-line-at-end-of-file* ]]; then
   # TODO Clean any empty characters
   # This is a weird one, not empty-lines or trailing-spaces related.
   # Reopening the file corrects it for now
   ed "$FILE"
   w
   q
  elif [[ $LINE == *"too many spaces"* ]] && [[ $LINE == *braces* ]]; then
   sed -i "${LINE_NUMBER}s/ *{ */{/g" "$FILE"
   sed -i "${LINE_NUMBER}s/ *} */}/g" "$FILE"
  fi
  # Remove the line with the error from the output log file
  # shellcheck disable=SC2094
  sed -i '1d' /tmp/temp_lint.txt
  # Cat the log file (can be muted, I liked seeing it for debugging purposes)
  echo 'the log file looks like this now...'
  # shellcheck disable=SC2094
  cat /tmp/temp_lint.txt
 # shellcheck disable=SC2094
 done </tmp/temp_lint.txt
}

function process_file {
 # Making sure the file is a yaml file
 if [[ "$1" == *.yaml ]] || [[ "$1" == *.yml ]]; then
  # Valid yaml file! Process it
  echo 'Valid yaml file :)'
  check_beginning_yaml
  run_yamllint "$1"
  loop_log_file
 else
  echo "Skipping $1, it is not a yaml file"
 fi
}

function check_beginning_yaml {
 # Missing the beginning of the file is a common mistake
 # Adding it now before running yamllint so that the line numbers
 # in the output file are accurate for processing other errors
 read -r firstline<"$FILE"
 if [[ $firstline != "---" ]]; then
  sed -i "1s/^/---\n/g" "$FILE"
 fi
}

function run_yamllint {
 # Run yamllint and extract output into a temp file
 yamllint -f parsable "$1" | tee /tmp/temp_lint.txt
}

########## BEGINNING OF THE SCRIPT ##########

# Only run the script if it is being called directly and not sourced.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
 version "$@"
fi
