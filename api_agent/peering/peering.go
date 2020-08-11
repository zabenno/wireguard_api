package peering

import (
	"agent/keypair"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
)

type Server struct {
	Endpoint_address string `json:"endpoint_address"`
	Endpoint_port    int    `json:"endpoint_port"`
	Public_key       string `json:"public_key"`
}

type Subnet struct {
	Allowed_ips string `json:"allowed_ips"`
	Lease       string `json:"lease"`
}

type Peering struct {
	Server Server `json:"server"`
	Subnet Subnet `json:"subnet"`
}

type Client struct {
	Client_name string `json:"client_name"`
	Server_name string `json:"server_name"`
	Public_key  string `json:"public_key"`
}

type PeeringInstance struct {
	api_server   string
	api_username string
	api_password string
	client_name  string
	server_name  string
	public_key   string
	private_key  string
}

//Used to create an instance of a client-server peering in local memory.
func New(api_server, api_username, api_password, client_name, server_name string) (PeeringInstance, error) {
	keypair, keypair_error := keypair.New(server_name)
	if keypair_error != nil {
		return PeeringInstance{}, keypair_error
	}
	peering_instance := PeeringInstance{api_server, api_username, api_password, client_name, server_name, keypair.Public_key, keypair.Private_key}
	return peering_instance, nil
}

//Creates an client-server peering instance with the wireguard_api.
func (peering PeeringInstance) Create_peer() error {
	json_peering_request := peering.generate_peering_request()
	return peering.submit_peering_request(json_peering_request)
}

//Creates a wireguard configuration file on the local file system for the client-server instance.
func (peering PeeringInstance) Create_config_file() error {
	peering_details, details_error := peering.get_peering_details()
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

//Creates the content that will be placed in the body of the REST API call to the wireguard_api server.
func (peering PeeringInstance) generate_peering_request() string {
	var client_request = Client{
		Client_name: peering.client_name,
		Server_name: peering.server_name,
		Public_key:  peering.public_key,
	}
	client_request_JSON, err := json.MarshalIndent(client_request, "", "	")
	if err != nil {
		log.Print(err)
	}
	return string(client_request_JSON)
}

//Submits a peering request to the wireguard_api server.
func (peering PeeringInstance) submit_peering_request(request_str string) error {
	url := peering.api_server + "/api/v1/client/add/"
	req, http_error := http.NewRequest(http.MethodPost, url, bytes.NewBuffer([]byte(request_str)))
	if http_error != nil {
		log.Print("Failed to create http request.")
		return http_error
	}
	req.Header.Set("Content-Type", "application/json;")
	req.SetBasicAuth(peering.api_username, peering.api_password)

	client := &http.Client{}
	resp, client_error := client.Do(req)
	if client_error != nil {
		log.Printf(fmt.Sprintf("Unable to connect to Wireguard api server at %s.", url), client_error)
		return client_error
	}

	if resp.StatusCode == 500 {
		log.Print(fmt.Sprintf("API server was not able to broker a connection to server %s.", peering.server_name))
		return errors.New("ApiServerError.")
	} else if resp.StatusCode == 400 {
		log.Print(fmt.Sprintf("Client sent bad request to server when attempting to register with server %s.", peering.server_name))
		return errors.New("RequestFormatError")
	} else if resp.StatusCode == 401 {
		log.Print("API server rejected credentials.")
		return errors.New("Unauthorised")
	} else if resp.StatusCode != 201 {
		log.Print(fmt.Sprintf("An unexpected error occured while registering with server %s.", peering.server_name))
		return errors.New("Unknown")
	}
	return nil
}

//Creates the contents of a wireguard configuration file for the client-server peering instance.
func (peering PeeringInstance) generate_conf(peering_details Peering) string {
	conf := fmt.Sprintf("[Interface]\nAddress = %s\nPrivateKey = %s\n\n[Peer]\nPublicKey = %s\nAllowedIPs = %s\nEndpoint = %s:%d",
		peering_details.Subnet.Lease, peering.private_key, peering_details.Server.Public_key, peering_details.Subnet.Allowed_ips,
		peering_details.Server.Endpoint_address, peering_details.Server.Endpoint_port)

	return conf
}

//Retrieves all information hosted by the wireguard_api server required to create a configuration file for the client-server peering instance.
func (peering PeeringInstance) get_peering_details() (Peering, error) {
	url := peering.api_server + "/api/v1/client/config/"
	var body = []byte(fmt.Sprintf("{\"client_name\": \"%s\", \"server_name\":\"%s\"}", peering.client_name, peering.server_name))
	req, http_error := http.NewRequest(http.MethodGet, url, bytes.NewBuffer(body))
	if http_error != nil {
		log.Print("Failed to create http request.")
		return Peering{}, http_error
	}

	client := &http.Client{}

	req.Header.Set("Content-Type", "application/json;")
	resp, client_error := client.Do(req)
	if client_error != nil {
		log.Printf(fmt.Sprintf("Unable to connect to Wireguard api server at %s.", url), client_error)
		return Peering{}, client_error
	}

	if resp.StatusCode == 500 {
		log.Print(fmt.Sprintf("Was unable to get peering config for connection to server %s.", peering.server_name))
		return Peering{}, errors.New("Failed")
	} else if resp.StatusCode == 401 {
		log.Print("API server rejected credentials.")
		return Peering{}, errors.New("Unauthorised")
	} else if resp.StatusCode != 200 {
		log.Print(fmt.Sprintf("An unexpected error occured while retrieving peering details with server %s.", peering.server_name))
		return Peering{}, errors.New("Unknown")
	}

	bodyBytes, read_error := ioutil.ReadAll(resp.Body)
	if read_error != nil {
		log.Print(read_error)
		return Peering{}, read_error
	}

	var jso Peering
	parsing_error := json.Unmarshal(bodyBytes, &jso)
	if parsing_error != nil {
		log.Print(parsing_error)
		return Peering{}, parsing_error
	}
	return jso, nil
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
