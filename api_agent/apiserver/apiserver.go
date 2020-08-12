package apiserver

import (
	"agent/apiv1"
	"agent/configparser"
	"agent/keypair"
	"agent/wgcli"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
)

type Server struct {
	cli             wgcli.Wg_Cli
	api             apiv1.API_Interface
	server_name     string
	public_key      string
	private_key     string
	endpointaddress string
	endpointport    int
	subnet          Subnet
}

type Subnet struct {
	NetworkAddress string
	NetworkMask    int
	NumReservedIps int
	AllowedIps     string
}

//Creates a new server instance in local memory.
func New(config configparser.Config) (Server, error) {
	keypair, keypair_error := keypair.New(config.Server.Name)
	if keypair_error != nil {
		return Server{}, keypair_error
	}
	cli, cli_error := wgcli.New()
	if cli_error != nil {
		return Server{}, cli_error
	}
	api := apiv1.New(config.ApiServer.Address, config.ApiServer.Username, config.ApiServer.Password)
	servers_subnet := Subnet{config.Server.Subnet.NetworkAddress, config.Server.Subnet.NetworkMask, config.Server.Subnet.NumReservedIps, config.Server.Subnet.AllowedIps}
	server := Server{cli, api, config.Server.Name, keypair.Public_key, keypair.Private_key, config.Server.EndpointAddress, config.Server.EndpointPort, servers_subnet}
	return server, nil
}

//Submits a peering request to the wireguard_api server.
func (server Server) Register_server() error {
	request_str, json_str_error := server.generate_peering_request()
	if json_str_error != nil {
		return json_str_error
	}
	return server.api.Add_server(request_str)
}

//Creates the content that will be placed in the body of the REST API call to the wireguard_api server.
func (server Server) generate_peering_request() (string, error) {
	var new_server_request = apiv1.NewServerRequest{
		ServerName:      server.server_name,
		NetworkAddress:  server.subnet.NetworkAddress,
		NetworkMask:     server.subnet.NetworkMask,
		PublicKey:       server.public_key,
		EndpointAddress: server.endpointaddress,
		EndpointPort:    server.endpointport,
		NReservedIps:    server.subnet.NumReservedIps,
		AllowedIps:      server.subnet.AllowedIps,
	}
	new_server_request_JSON, json_error := json.MarshalIndent(new_server_request, "", "	")
	if json_error != nil {
		log.Print("Failed to create json peering request.")
		return "", json_error
	}
	return string(new_server_request_JSON), nil
}

//Returns bool based on if the server is registered with the wireguard api or not.
func (server Server) Server_is_registered() (bool, error) {
	return server.api.Get_server_existance(server.server_name)
}

func (server Server) Create_interface() error {
	return server.cli.Create_interface(server.server_name)
}

//Refreshes the in memory configuration of the wireguard server.
func (server Server) Sync_wireguard_conf() error {
	return server.cli.Sync_wireguard_conf(server.server_name)
}

//Updates the on disk configuration for the wireguard server.
func (server Server) Update_config_file(config string) error {
	file_path := fmt.Sprintf("/etc/wireguard/%s.conf", server.server_name)

	write_error := ioutil.WriteFile(file_path, []byte(config), 0600)
	if write_error != nil {
		log.Print("Failed to write contents to file.")
		return write_error
	}
	return nil
}

//Creates the contents for the configuration file to be used by `wg syncconf`
func (server Server) Get_config_contents() (string, error) {
	response := server.get_interface_config()
	peers, err := server.api.Get_server_peers(server.server_name)
	if err != nil {
		return "", err
	}
	for index := range peers.Peers {
		response += fmt.Sprintf("[Peer]\nPublicKey = %s\nAllowedIPs = %s/32\n\n", peers.Peers[index].Publickey, peers.Peers[index].IPAddress)
	}
	return response, nil
}

//Creates the contents for the interface section of the wireguard server configuration
func (server Server) get_interface_config() string {
	response := "[Interface]\n"
	response += fmt.Sprintf("PrivateKey = %s\n", server.private_key)
	response += fmt.Sprintf("ListenPort = %d\n", server.endpointport)
	return response
}

//Creates the wireguard configuration file for wg-quick to work.
func (server Server) Get_wgquick_config() (string, error) {
	response := server.get_interface_config()
	wg_ip, wg_ip_error := server.api.Get_server_wg_ip(server.server_name)
	if wg_ip_error != nil {
		return "", wg_ip_error
	} else {
		response += fmt.Sprintf("Address = %s/%d\n", wg_ip, server.subnet.NetworkMask)
		return response, nil
	}
}
