package peering

import (
	"agent/apiv1"
	"agent/keypair"
	"fmt"
	"io/ioutil"
	"log"
	"os"
)

type PeeringInstance struct {
	api         apiv1.API_Interface
	client_name string
	server_name string
	public_key  string
	private_key string
}

//Used to create an instance of a client-server peering in local memory.
func New(api_server, api_username, api_password, client_name, server_name string) (PeeringInstance, error) {
	keypair, keypair_error := keypair.New(server_name)
	if keypair_error != nil {
		return PeeringInstance{}, keypair_error
	}
	api_server_instance := apiv1.New(api_server, api_username, api_password)
	peering_instance := PeeringInstance{api_server_instance, client_name, server_name, keypair.Public_key, keypair.Private_key}
	return peering_instance, nil
}

//Creates an client-server peering instance with the wireguard_api.
func (peering PeeringInstance) Create_peer() error {
	return peering.api.Add_client(peering.server_name, peering.client_name, peering.public_key)
}

//Creates a wireguard configuration file on the local file system for the client-server instance.
func (peering PeeringInstance) Create_config_file() error {
	peering_details, details_error := peering.api.Get_client_details(peering.server_name, peering.client_name)
	if details_error == nil {
		config_file_contents := peering.generate_conf(peering_details)
		write_error := peering.write_config_to_file(config_file_contents)
		if write_error != nil {
			return write_error
		} else {
			return nil
		}
	} else {
		return details_error
	}
}

//Checks for an existing configuration file for the client-server peering instance.
func (peering PeeringInstance) Check_peering_existance() bool {
	filename := fmt.Sprintf("/etc/wireguard/%s.conf", peering.server_name)
	_, err := os.Stat(filename)
	if os.IsNotExist(err) {
		return false
	}
	return true
}

//Creates the contents of a wireguard configuration file for the client-server peering instance.
func (peering PeeringInstance) generate_conf(peering_details apiv1.Peering) string {
	conf := fmt.Sprintf("[Interface]\nAddress = %s\nPrivateKey = %s\n\n[Peer]\nPublicKey = %s\nAllowedIPs = %s\nEndpoint = %s:%d",
		peering_details.Subnet.Lease, peering.private_key, peering_details.Server.Public_key, peering_details.Subnet.Allowed_ips,
		peering_details.Server.Endpoint_address, peering_details.Server.Endpoint_port)

	return conf
}

//Writes a configuration file to disk for the client-server peering instance.
func (peering PeeringInstance) write_config_to_file(config string) error {
	file_path := fmt.Sprintf("/etc/wireguard/%s.conf", peering.server_name)

	write_error := ioutil.WriteFile(file_path, []byte(config), 0600)
	if write_error != nil {
		log.Print("Failed to write contents to file.")
		return write_error
	}
	return nil
}
