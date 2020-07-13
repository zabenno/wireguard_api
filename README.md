# wireguard_api
A REST API server to manage clients and servers peering.
## Warning: WIP
This is a work in progress, expect further documentation and changes to follow. These changes will include database changes.

## Assumptions
All testing for this has been done on an Ubuntu 20.04 host.

## Setup
Within the project directory you will need to run the following commands to create the appropriate python venv.
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install libpq-dev python3-venv -y 
./lab_env/bin/pip install pylint
./lab_env/bin/pip install psycopg2
```

## API Calls

### /api/v1/server/add/
This call is to add a server to the database.

#### Call Content
```json
{
    "server_name":"name",
    "network_address":"192.168.4.0",
    "network_mask":24,
    "public_key":"XXYYXXZZ",
    "endpoint_address":"192.168.0.99",
    "endpoint_port":5128,
    "n_reserved_ips":20
}
```
#### Responses
HTTP: 201, 500

