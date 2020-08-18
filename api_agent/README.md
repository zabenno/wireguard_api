# Overview
This agent will negoitate with the wireguard_api server on behalf of either a wireguard server or client depending on it's configuration. The agents assumes that wireguard has been installed and it has access to both the `wg-quick` and `wg syncconf` commmands. If these are not present the agent will fail.

The agent handles both the import of existing keys found in `/etc/wireguard_api/` or the creation of the keys where it stores them within the same folder with the file permissions `0600`. The keypairs are named based on the server providing the wireguard session in the format `<server_name>.pub` and `.<server_name>.priv`. For a client this will mean a pair per entry under `peers` in the configuration file, for a server this will be the value within `server:name`.

## Status
There is still a significant amount of refactoring work required to assist in future maintainability however the agent is now fully functional and could be built and deployed as is.

All code was tested on:
* Ubuntu 20.04: go1.13.8 (from source)
* Ubuntu 18.04: (prebuilt binary)

## Build
To setup the environment to build or run the agent enter the following commands:
Note: `go mod` was introduced in version 1.11 of golang.
```bash
apt install golang -y
go get gopkg.in/yaml.v2
go mod init agent
```
To build: `go build agent.go`
To run: `go run agent.go`

## Server Mode
When configured as a server the agent will take full responsibility for the handling of the negotiation with the wireguard api service as well as the creation and maintainance of the interface. It achieves this by first creating a configuration file supported by wg-quick to create the interface, then continuosly refreshing a config file supported by wg syncconf that includes the client list. Currently the agent does not support the destruction of old interfaces and this must be done manually. 

Please note: I have made the assumption you will not be needing a wireguard server instance anymore if you have deleted the keypair and config file on it's host. In the event that you have deleted the old keypair and configuration file and wish to rebuild the server, you will need to manually remove the server from the wireguard api server via the `/api/v1/server/delete/` call.
### Configuration example
```yaml
name: ""
type: "client | server"
api_server:
    address: ""
    username: ""
    password: ""
server:
    name: ""
    endpoint_address: ""
    endpoint_port: 5128
    refresh_frequency: 20
    subnet:
        network_address: ""
        network_mask: 24
        num_reserved_ips: 20
        allowed_ips: ""
```
## Client Mode
When configured as a client the agent will attempt negotiate and create a valid wireguard configuration file for each server in it's peers list. These configuraion files can then be used to establish a wireguard session by running the command `wg-quick up /etc/wireguard/<server_name>.conf`. I made the decision not to include the creation of the interface within the agent as customisation of the interface may be desired.
### Configuration example
```yaml
name: ""
type: "client | server"
api_server:
    address: "https://api_server_location"
    username: "User for auth"
    password: "Password for auth"
peering_list:
    - server_name: ""
```