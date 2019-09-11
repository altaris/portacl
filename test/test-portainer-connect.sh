#!/bin/sh

PORTAINER_API=http://localhost:9001/api

echo "Connecting to $PORTAINER_API"

PORTAINER_TOKEN=$(
    curl -s -H "Accept:application/json" -X POST 		\
    -d '{"Username": "admin", "Password": "password"}' 	\
    "$PORTAINER_API"/auth | jq -r .jwt
)

portainer_api_call() {
    # Example: portainer_api_call "POST" "/auth" "{...}"
    curl -s -X "$1" "$PORTAINER_API$2"              \
        -H "Accept:application/json"                \
        -H "Authorization: Bearer $PORTAINER_TOKEN" \
        -d "$3"
}
