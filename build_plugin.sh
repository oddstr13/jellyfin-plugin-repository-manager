#!/bin/bash
MY=$(dirname $(realpath -s "${0}"))
JPRM="python3 $MY/jprm.py"

PLUGIN=${1:-${PLUGIN:-.}}

ARTIFACT_DIR=${ARTIFACT_DIR:-"${MY}/artifacts"}
mkdir -p "${ARTIFACT_DIR}"

JELLYFIN_REPO=${JELLYFIN_REPO:-$MY/test_repo}
JELLYFIN_REPO_URL=${JELLYFIN_REPO_URL:-http://10.79.1.0:8080}

# Each segment of the version is a 16bit number.
# Max number is 65535.
VERSION_SUFFIX=${VERSION_SUFFIX:-$(date -u +%Y.%m%d.%H%M)}

meta_version=$(grep -Po '^ *version: * "*\K[^"$]+' "${PLUGIN}/build.yaml")
VERSION=${VERSION:-$(echo $meta_version | sed 's/\.[0-9]*\.[0-9]*\.[0-9]*$/.'"$VERSION_SUFFIX"'/')}

zipfile=$($JPRM --verbosity=debug plugin build "${PLUGIN}" --output="${ARTIFACT_DIR}" --version="${VERSION}") && {
    $JPRM repo add --url=${JELLYFIN_REPO_URL} "${JELLYFIN_REPO}" "${zipfile}"
}
exit $?
