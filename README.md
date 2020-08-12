# wireguard_api
This repo contains the code for a Python3 based web API service that allows for the brokering of connections between wireguard servers and their clients. It also includes a Golang based agent that negotiates with the broker the details of a hosts wireguard connection.

## Overview
The goal of this project is to create an automated way of brokering connections between Wireguard clients and their servers.
Servers are fully managed via the agent with their interface created and regularly updated.
Currently for clients, the agent only generates the configuration files required to create/configure wireguard interfaces. The creation of these interfaces is not handled by the agent, for this, see the wireguard command `wg-quick`. 

Warnings: 
* Code really needs some refactoring.
* TLS is not handled by this app so a proxy is a must.

Note:
* All testing for this project has been done on Ubuntu 20.04, within a python3.8 venv connecting to the docker image postgres:12.3.

## Design Descisions
### Pull From Server
Updates to a WireGuard servers client list will be done via a pull from the server. This is because the intention of this API is for it to be used in conjuction with the wg-tools package, specifically the `wg syncconf` command, to avoid disrupting existing client connections when adding a new client. As the documentation for this command says it is "much less efficient" I have assumed it would be best to do this on a time interval basis, e.g. every 30 seconds, to avoid refreshing the client list for every new client addition/deletion.

### Clients
A client should be thought of as a single hostname, that has one or multiple peerings.

Client assumptions:
* A client can be peered to multiple servers but can only have one concurrent peering to any single server.
* If a client is deleted by name all instances of peering are also deleted.
* A client must have a peering instance to exist.
* A client will be directly requesting the API for changes to itself.

### Security
Currently the project requires a specified shared username/password for all POST requests and assumes it is behind a TLS proxy.

## Test Setup
API Brokering Service:
* Create your database e.g. `docker run -it -e POSTGRES_PASSWORD=changeme123 -p 5432:5432 postgres:12.3`
* Build a local docker image of the web api: `docker build -t test .`
* Create the missing files listed within docker-compose.yml. See https://gist.github.com/fntlnz/cf14feb5a46b2eda428e000157447309 for a guide on making ssl certs.
* Create a docker swarm `docker swarm init`
* Deploy docker services using the docker-compose.yml file `docker stack deploy test -c docker-compose.yml`

For details on building/running the agent, check the agents readme.

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
HTTP: 201, 400, 500
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
HTTP: 201, 400, 500
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
### /api/v1/server/exists/
This call is to check if a server exists.
#### Call Content
```json
{
    "server_name":"name"
}
```
#### Responses
HTTP: 200, 404