#!/bin/sh
set -e

ls $WORKDIR/.git > /dev/null && cd $WORKDIR || cd /app
echo working from `pwd`
echo "GIT_REPO: $GIT_REPO"
echo "GIT_BRANCH: $GIT_BRANCH"

if [ ! -z "$GIT_REPO" ]; then
    rm -rf /remote || true && git clone $GIT_REPO /remote && cd /remote;
    if [ ! -z "$GIT_BRANCH" ]; then
        git checkout origin/$GIT_BRANCH
    fi
    cd /remote && napa eligrey/FileSaver.js:file-saver && npm install && node node_modules/.bin/gulp
else
    ( cd /repos/os-viewer && npm install ) || true
    ( cd /repos/os-viewer && node node_modules/gulp/bin/gulp.js ) || true
fi

npm start
