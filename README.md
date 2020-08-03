# wireguard_api
A REST API server to broker basic connections between clients and servers.

This documentation is in real need of a refresh, will look at doing this in the near future.

## Overview
The goal of this project is to create an automated way of brokering connections between Wireguard clients and their servers.
Servers are fully managed via the agent with their interface created and regularly updated.
Currently for clients, the agent only generates the configuration files required to create/configure wireguard interfaces. The creation of these interfaces is not handled by the agent, for this, see the wireguard command `wg-quick`. 

Warnings: 
* Code really needs a clean up. Some refactoring, authentication, and improved error handling and logging.
* User data passed to SQL queries is sanitised, however few checks are performed to ensure input data makes contextual sense.
* Due to the way the `wg syncconf` parses config, an invalid client public key will prevent the server from refreshing it's client list. This will fail with a misleading error suggesting the problem lies within the first lines of the generated file.
* TLS is not handled by this app so a proxy is a must.

Note:
* All testing for this project has been done on Ubuntu 20.04, within a python3.8 venv connecting to the docker image postgres:12.3.

## Design Descisions
### Pull From Server
Updates to a WireGuard servers client list will be done via a pull from the server. This is because the intention of this API is for it to be used in conjuction with the wg-tools package, specifically the `wg syncconf` command, to avoid disrupting existing client connections when adding a new client. As the documentation for this command says it is "much less efficient" I have assumed it would be best to do this on a time interval basis, e.g. every 30 seconds, to avoid refreshing the client list for every new client addition/deletion.

### Clients
A client should be thought of as a single entity, consisting of one or multiple peerings.

Client assumptions:
* A client can be peered to multiple servers but can only have one concurrent peering to any single server.
* If a client is deleted by name all instances of peering are also deleted.
* A client must have a peering instance to exist.
* A client will be directly requesting the API for changes to itself.

### Security
Currently the project requires a specified shared username/password for all POST requests and assumes it is behind a TLS proxy.

## Test Setup
To run as is you'll need to create a postgres db with the following command.
```bash
docker run -it -e POSTGRES_PASSWORD=changeme123 -p 5432:5432 postgres:12.3
```
To load in some test data, run `python example.py` with the correct parameters.

To demo the agents you must have golang installed you can then run the agents with `go run /path/to/agent.go`

To run the app you will need to create the missing files listed within docker-compose.yml.

Follow this guide to create your ssl certs: https://gist.github.com/fntlnz/cf14feb5a46b2eda428e000157447309

This compose file requires a swarm to function. Run `docker swarm init` before running `docker stack deploy test -c docker-compose.yml`.

You will also need to build the docker container locally with `docker build -t test .`

If you wish to run the app directly on your host run the following commands from wiithin the project directory.
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install libpq-dev python3-venv -y 
./lab_env/bin/pip install pylint
./lab_env/bin/pip install psycopg2
```

PS: Sorry if some instructions are missing.

## Agent Configuration
The agent can be configured as either a server or a client with the following parameters.
```yaml
name: ""
type: "client | server"
api_server:
    address: "https://api_server_location"
    username: "User for auth"
    password: "Password for auth"
server:         #Required for server.
    name: ""
    private_key: ""
    public_key: ""
    endpoint_address: ""
    endpoint_port: 5128
    subnet:
        network_address: ""
        network_mask: ""
        num_reserved_ips: 20
        allowed_ips: ""
peering_list:   #Required for client.
    server_name: ""
    public_key: ""
    private_key: ""
```

## API Calls

### /api/v1/client/list_all
This call is to list the basic information about every peering instance everying client has.
#### Call Content
None
#### Response
HTTP: 200
```json
{
    "client1": {
        "peering1": {
            "public_key": "AABBCCDDEEFF",
            "server": "server1"
        }
    }
}
```
HTTP: 500

### /api/v1/server/list_all
This call is to list the basic information about every defined server.
#### Call Content
None
#### Response
HTTP: 200
```json
{
    "server1": {
        "endpoint_address": "xxx.xxx.xxx.xxx",
        "endpoint_port": 1234,
        "public_key": "AABBCCDDEEFF"
    }
}
```
HTTP: 500

### /api/v1/server/config/
This call is to pull down the information required for configuring the server to connect to registered peers.
#### Call Content
```json
{
    "server_name":"name"
}
```
#### Responses
HTTP: 200
```json
{
    "peers":[
        {
        "ip_address": "xxx.xxx.xxx.xxx",
        "public_key": "AABBCCDDEEFF"
        }
    ]
}
```
HTTP: 500

HTTP: 404
### /api/v1/server/wireguard_ip/
This call is to pull down the information required for configuring the server to connect to registered peers.
#### Call Content
```json
{
    "server_name":"name"
}
```
#### Responses
HTTP: 200
```json
{
    "server_wg_ip": "xxx.xxx.xxx.xxx"
}
```
HTTP: 500
### /api/v1/client/config/
This call is to pull down the configuration of a specified client-server peer.
#### Call Content
```json
{
    "client_name":"name",
    "server_name":"name"
}
```
#### Responses
HTTP: 200
```json
{
    "server":{
        "endpoint_address":"xxx.xxx.xxx.xxx",
        "endpoint_port": 1234,
        "public_key": "BBAACCDDEEFF"
    },
    "subnet":{
        "allowed_ips": "xxx.xxx.xxx.xxx/yy",
        "lease": "xxx.xxx.xxx.xxx"
    }
}
```
HTTP: 500

### /api/v1/server/add/
This call is to add a server to the database.

#### Call Content
```json
{
    "server_name":"name",
    "network_address":"xxx.xxx.xxx.xxx",
    "network_mask":24,
    "public_key":"XXYYXXZZ",
    "endpoint_address":"xxx.xxx.xxx.xxx",
    "endpoint_port":5128,
    "n_reserved_ips":20,
    "allowed_ips": "xxx.xxx.xxx.xxx/yy"
}
```
#### Responses
HTTP: 201, 500
### /api/v1/client/add/
This call is to add a client linked to an existing server the database.
Note: Recalling will delete the server-client peer and create a new one.
#### Call Content
```json
{
    "client_name":"name",
    "server_name":"name",
    "public_key":"XXYYXXZZ",
}
```
#### Responses
HTTP: 201, 500
### /api/v1/client/delete/
This call is to delete all instances of a single client from any servers.
Note: This also frees the IP leases from the server.
#### Call Content
```json
{
    "client_name":"name"
}
```
#### Responses
HTTP: 200, 500
### /api/v1/server/delete/
This call is to delete a server.
Note: This also remove all instances of clients that are attached to this server. In the case this is the only server a client is attached to, it will also delete the client.
#### Call Content
```json
{
    "server_name":"name"
}
```
#### Responses
HTTP: 200, 500
### /api/v1/server/remove_peer/
This call is to remove a single client from a server.
Note: In the case this is the only server a client is attached to, it will also delete the client.
#### Call Content
```json
{
    "client_name":"name",
    "server_name":"name"
}
```
#### Responses
HTTP: 200, 500
