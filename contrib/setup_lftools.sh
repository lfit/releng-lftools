#!/bin/bash
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

# This script sets up a new lftools dev environment. It expects one arg, the
# associated Jira issue ID, e.g. RELENG-1234 (or another unique ID)

# A top-level directory is created ($HOME/Code), and in it, a .venv-lftools-$1
# for each Jira issue. It then checks out lftools from git (using your 
# gitreview.username) into a directory named lftools-$1.

# Once completed, activate the venv to start hacking.
# While in the venv, the working branch supercedes any other
# lftools in your library path, and the lftools cli command also
# supercedes any other installed lftools.

die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -eq 1 ] || die "Pass a Jira issue (or another unique identifier) as an argument."

if [ ! -d "$HOME/Code" ]; then
	echo "$HOME/Code does not exist, creating it..."
	mkdir $HOME/Code
fi


VENV_DIR=".venv-lftools-$1"
GIT_REVIEW_USERNAME=`git config --global gitreview.username`
PY3=`which python3`

virtualenv -p $PY3 $VENV_DIR

cat <<EOF > $VENV_DIR/bin/lftools
#!$HOME/Code/$VENV_DIR/bin/python3

import re
import sys

from lftools.cli import main


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())

EOF

chmod +x $VENV_DIR/bin/lftools

git clone "https://$GIT_REVIEW_USERNAME@gerrit.linuxfoundation.org/infra/a/releng/lftools" lftools-$1 && (cd "lftools-$1" && mkdir -p .git/hooks && curl -Lo `git rev-parse --git-dir`/hooks/commit-msg https://$GIT_REVIEW_USERNAME@gerrit.linuxfoundation.org/infra/tools/hooks/commit-msg; chmod +x `git rev-parse --git-dir`/hooks/commit-msg)

source $VENV_DIR/bin/activate
cd lftools-$1
pip install -r requirements.txt
pip install -r requirements-test.txt
ln -s $HOME/Code/lftools-$1/lftools/ $HOME/Code/$VENV_DIR/lib/python3.7/site-packages/lftools
