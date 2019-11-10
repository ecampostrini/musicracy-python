#!/usr/bin/env bash
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
CONFIG_REGEX="([A-Z0-9_]+)=[^\#]+\#\s*(.*)$"

if [ `basename ${ROOT}` != "musicracy" ]; then
  echo "`basename $0` must be run inside Musicracy source tree"
  exit 1
fi

cd ${ROOT}

declare -A PROXIES
counter=0
for proxy in $(ls ${ROOT}/backend/proxies); do
  PROXIES[${counter}]="${proxy}"
  counter=$((counter + 1))
done

proxy_num=-1
while true; do
  echo "Available proxies: "
  for index in ${!PROXIES[@]}; do
    echo "${index} - ${PROXIES[${index}]}"
  done
  read -p "Please select which proxy to configure (0 - `expr ${#PROXIES[@]} - 1`): " proxy_num

  ([ ${proxy_num} -lt 0 ] || [ ${proxy_num} -ge ${#PROXIES[@]} ]) && continue

  break
done

PROXY_ROOT="${ROOT}/backend/proxies/${PROXIES[${proxy_num}]}"
CONFIG_TEMPLATE="${PROXY_ROOT}/config.tmpl"
if [ ! -f $CONFIG_TEMPLATE ]; then
  echo "Proxy configuration template not found: ${CONFIG_TEMPLATE}"
  exit 1
fi

declare -A CONFIG
while IFS= read -r line; do
  if [[ $line =~ $CONFIG_REGEX ]]; then
    CONFIG[${BASH_REMATCH[1]}]=${BASH_REMATCH[2]}
  fi
done < $CONFIG_TEMPLATE

printf "\nPlease complete the config with the required values: \n"
for key in ${!CONFIG[@]}; do
  read -p "${key} (${CONFIG[${key}]}): " val
  export ${key}="\"${val}\""
done

CONFIG_FILE="${PROXY_ROOT}/config.py"
envsubst < ${CONFIG_TEMPLATE} > ${CONFIG_FILE}

printf "\nConfiguration file written to: ${CONFIG_FILE}\n" 
