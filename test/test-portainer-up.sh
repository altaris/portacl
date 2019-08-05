#!/bin/sh

ADMIN_PASSWORD='$2y$05$cS8SdlD8BHTdGFxd1IouVe8MRl3y7x/jAOpPvaTn.1KLEC7QpEqca'

echo "Starting portainer"
sudo docker run --detach                                \
    --name portacl-test-portainer						\
    --publish 9000:9000									\
    --volume /var/run/docker.sock:/var/run/docker.sock	\
    portainer/portainer --admin-password="$ADMIN_PASSWORD"

sleep 2

TOKEN=$(
    curl -s -H "Accept:application/json" -X POST 		\
    -d '{"Username": "admin", "Password": "password"}' 	\
    http://localhost:9000/api/auth | jq -r .jwt
)

_new_user() {
    curl -s -X POST http://localhost:9000/api/users                          \
        -H "Accept:application/json"                                         \
        -H "Authorization: Bearer $TOKEN"                                    \
        -d "{\"Username\": \"$1\", \"Password\": \"password\", \"Role\": 2}" \
        > /dev/null
}

_new_team() {
    curl -s -X POST http://localhost:9000/api/teams  \
        -H "Accept:application/json"                 \
        -H "Authorization: Bearer $TOKEN"            \
        -d "{\"Name\": \"$1\"}"                      \
        > /dev/null
}

_add_user_to_team() {
    curl -s -X POST http://localhost:9000/api/team_memberships \
        -H "Accept:application/json"                           \
        -H "Authorization: Bearer $TOKEN"                      \
        -d "{\"UserID\": $1, \"TeamID\": $2, \"Role\": 2}"     \
        > /dev/null
}

echo "Adding users"
_new_user "bob"
_new_user "carol"
_new_user "daniel"

echo "Adding teams"
_new_team "development"
_new_team "qa"
_new_team "production"

echo "Adding users to teams"
_add_user_to_team 2 1
_add_user_to_team 3 1
_add_user_to_team 3 2
_add_user_to_team 3 3
_add_user_to_team 4 3

echo "Done"