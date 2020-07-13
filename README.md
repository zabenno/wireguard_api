# wireguard_api
A REST API server to broker connections between clients and servers.

## Overview
The goal of this project is to create an automated way of brokering connections between Wireguard clients and their servers. This project could be greatly expanded and has a decent amount of assumptions.

Warnings: 
* This project is still a work in progress, futher documentation and code changes should be expected. Code could really use some clean up.
* All testing for this project has been done on Ubuntu 20.04, within a python3.8 venv connecting to the docker image postgres:12.3.
* Currently this project does not support any type of authentication meaning anyone with access to the API can do anything.
* TLS is not handled by this app so a proxy is a must.

Technical goals:
* All state is offloaded to a Postgres database.
* Dockerised.
* HTTPS to be done via proxy.

## Design Descisions
### Pull From Server
Updates to a WireGuard servers client list will be done via a pull from the server. This is because the intention of this API is for it to be used in conjuction with the wg-tools package, specifically the `wg syncconf` command, to avoid disrupting existing client connections when adding a new client. As the documentation for this command says it is "much less efficient" I have assumed it would be best to do this on a time interval basis, e.g. every 30 seconds, to avoid refreshing the client list for every new client addition/deletion.

### Clients
A client should be thought of as a single entity, consisting of one or multiple peerings.

Client assumptions:
* A client can be peered to multiple servers but can only have one concurrent peering to any server.
* If a client is deleted by name all instances of peering are also deleted.
* A client must have a peering instance to exist.
* A client will be directly requesting the API for changes to itself.

### Security
Currently the project assumes that authentication and encryption will be dealt with either via a proxy or not required.

## Setup
Within the project directory you will need to run the following commands to create the appropriate python venv.
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install libpq-dev python3-venv -y 
./lab_env/bin/pip install pylint
./lab_env/bin/pip install psycopg2
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
    "peer1":{
        "ip_address": "xxx.xxx.xxx.xxx",
        "public_key": "AABBCCDDEEFF"
    }
}
```
HTTP: 500

HTTP: 404
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
        "allowed_ips": "" | null,
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
    "n_reserved_ips":20
}
```
#### Responses
HTTP: 201, 500
### /api/v1/client/add/
This call is to add a client linked to an existing server the database
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