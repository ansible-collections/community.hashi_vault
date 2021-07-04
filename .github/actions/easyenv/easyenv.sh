#!/usr/bin/env bash
while IFS= read -r line ; do
    eval "$line"
    __var=${line%%=*}
    echo "$line"
    echo "${__var}"
    echo "${!__var}"
    echo "${__var}=${!__var}" >> "${GITHUB_ENV}"
done
