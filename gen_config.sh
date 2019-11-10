#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/esteban/projects/musicracy"
CONFIG_REGEX="([A-Z0-9_]+)=[^\#]+\#\s*(.*)$"

declare -A PROXIES
function print_proxies() {
  echo "Available proxies: "
  for index in ${!PROXIES[@]}; do
    echo "${index} - ${PROXIES[${index}]}"
  done
  read -p "Please select which proxy to configure (0 - `expr ${#PROXIES[@]} - 1`): " proxy_num

}

counter=0
for proxy in $(ls ${ROOT}/backend/proxies); do
  PROXIES[${counter}]="${proxy}"
  counter=$((counter + 1))
done

print_proxies

PROXY_ROOT="${ROOT}/backend/proxies/${PROXIES[${proxy_num}]}"
CONFIG_TEMPLATE="${PROXY_ROOT}/config.tmpl"
if [ ! -f $CONFIG_TEMPLATE ]; then
  echo "Proxy configuration template not found: ${CONFIG_TEMPLATE}"
  exit 1
fi

declare -A CONFIG
while IFS= read -r line; do
  if [[ $line =~ $CONFIG_REGEX ]]; then
    #echo "${BASH_REMATCH[1]}: ${BASH_REMATCH[2]}"
    CONFIG[${BASH_REMATCH[1]}]=${BASH_REMATCH[2]}
  fi
done < $CONFIG_TEMPLATE

printf "\nPlease enter the required config: \n"
for key in ${!CONFIG[@]}; do
  read -p "${key} (${CONFIG[${key}]}): " val
  export ${key}="\"${val}\""
done

CONFIG_FILE="${PROXY_ROOT}/config.py"
envsubst < ${CONFIG_TEMPLATE} > ${CONFIG_FILE}

printf "\nConfiguration file written to: ${CONFIG_FILE}\n" 
