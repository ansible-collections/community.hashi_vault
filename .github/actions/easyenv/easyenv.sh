#!/usr/bin/env bash
while IFS= read -r line ; do
    if [[ "$line" =~ [^[:space:]] ]] ; then
        eval "$line"
        __var=${line%%=*}
        echo "${__var}=${!__var}" >> "${GITHUB_ENV}"
    fi
done
