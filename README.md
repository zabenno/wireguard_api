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