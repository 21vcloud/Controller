#!/bin/bash
set -o errexit

kolla_set_configs

CMD=$(cat /run_command)
ARGS=""

. kolla_extend_start

echo "Running command: '${CMD}${ARGS:+ $ARGS}'"
exec ${CMD} ${ARGS}
