#!/bin/sh

ADMIN_PASSWORD='$2y$05$cS8SdlD8BHTdGFxd1IouVe8MRl3y7x/jAOpPvaTn.1KLEC7QpEqca'

echo "Starting portainer"
sudo docker run --detach                                \
    --name portacl-test-portainer						\
    --publish 9001:9000									\
    --volume /var/run/docker.sock:/var/run/docker.sock	\
    portainer/portainer --admin-password="$ADMIN_PASSWORD"

sleep 2

# shellcheck disable=SC1091
. "$(cd "$(dirname "$0")" && pwd)/test-portainer-connect.sh"

portainer_new_user() {
    portainer_api_call "POST" "/users"                                    \
        "{\"Username\": \"$1\", \"Password\": \"password\", \"Role\": 2}" \
        > /dev/null
}

portainer_new_team() {
    portainer_api_call "POST" "/teams"  \
        "{\"Name\": \"$1\"}"            \
        > /dev/null
}

portainer_add_user_to_team() {
    portainer_api_call "POST" "/team_memberships"       \
        "{\"UserID\": $1, \"TeamID\": $2, \"Role\": 2}" \
        > /dev/null
}

portainer_add_local_endpoint() {
    curl -s -X "POST" "$PORTAINER_API/endpoints"    \
        -H "Authorization: Bearer $PORTAINER_TOKEN" \
        -F "Name=\"local\"" -F "EndpointType=1"     \
        > /dev/null
}

echo "Adding users"
portainer_new_user "bob"
portainer_new_user "carol"
portainer_new_user "daniel"

echo "Adding teams"
portainer_new_team "development"
portainer_new_team "qa"
portainer_new_team "production"

echo "Adding users to teams"
portainer_add_user_to_team 2 1
portainer_add_user_to_team 3 1
portainer_add_user_to_team 3 2
portainer_add_user_to_team 3 3
portainer_add_user_to_team 4 3

echo "Adding local endpoint"
portainer_add_local_endpoint

echo "Done"