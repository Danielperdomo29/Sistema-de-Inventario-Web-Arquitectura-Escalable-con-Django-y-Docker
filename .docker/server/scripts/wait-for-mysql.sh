#!/bin/bash
# Espera a que MySQL esté disponible antes de ejecutar el comando
set -e

HOST="${MYSQL_HOST:-mysql}"
PORT="${MYSQL_PORT_INTERNAL:-3306}"
MAX_RETRIES="${MYSQL_WAIT_RETRIES:-30}"
DELAY="${MYSQL_WAIT_DELAY:-2}"

count=0
while [ $count -lt $MAX_RETRIES ]; do
    count=$((count + 1))
    
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$HOST/$PORT" 2>/dev/null; then
        sleep 2
        exec "$@"
    fi
    
    sleep $DELAY
done

exit 1
