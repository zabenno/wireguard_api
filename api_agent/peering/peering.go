package peering

import (
	"agent/keypair"
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
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
func New(api_server, api_username, api_password, client_name, server_name string) PeeringInstance {
	keypair := keypair.New(server_name)
	peering_instance := PeeringInstance{api_server, api_username, api_password, client_name, server_name, keypair.Public_key, keypair.Private_key}
	return peering_instance
}

//Creates an client-server peering instance with the wireguard_api.
func (peering PeeringInstance) Create_peer() {
	json_peering_request := peering.generate_peering_request()
	peering.submit_peering_request(json_peering_request)
}

//Creates a wireguard configuration file on the local file system for the client-server instance.
func (peering PeeringInstance) Create_config_file() {
	peering_details := peering.get_peering_details()
	config_file_contents := peering.generate_conf(peering_details)
	peering.write_config_to_file(config_file_contents)
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
		panic(err)
	}
	return string(client_request_JSON)
}

//Submits a peering request to the wireguard_api server.
func (peering PeeringInstance) submit_peering_request(request_str string) {
	url := peering.api_server + "/api/v1/client/add/"
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewBuffer([]byte(request_str)))
	if err != nil {
		panic(err)
	}
	req.Header.Set("Content-Type", "application/json;")
	req.SetBasicAuth(peering.api_username, peering.api_password)

	client := &http.Client{}
	resp, err := client.Do(req)

	if err != nil {
		panic(err)
	}
	if resp.StatusCode != 201 {
		panic(resp.StatusCode)
	}
}

//Creates the contents of a wireguard configuration file for the client-server peering instance.
func (peering PeeringInstance) generate_conf(peering_details Peering) string {
	conf := fmt.Sprintf("[Interface]\nAddress = %s\nPrivateKey = %s\n\n[Peer]\nPublic_key = %s\nAllowedIPs = %s\nEndpoint = %s:%d",
		peering_details.Subnet.Lease, peering.private_key, peering_details.Server.Public_key, peering_details.Subnet.Allowed_ips,
		peering_details.Server.Endpoint_address, peering_details.Server.Endpoint_port)

	return conf
}

//Retrieves all information hosted by the wireguard_api server required to create a configuration file for the client-server peering instance.
func (peering PeeringInstance) get_peering_details() Peering {
	url := peering.api_server + "/api/v1/client/config/"
	var body = []byte(fmt.Sprintf("{\"client_name\": \"%s\", \"server_name\":\"%s\"}", peering.client_name, peering.server_name))
	req, err := http.NewRequest(http.MethodGet, url, bytes.NewBuffer(body))
	if err != nil {
		panic(err)
	}

	client := &http.Client{}

	req.Header.Set("Content-Type", "application/json;")
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}

	bodyBytes, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	bodyStr := string(bodyBytes)

	bytes := []byte(bodyStr)
	var jso Peering
	peering_err := json.Unmarshal(bytes, &jso)
	if peering_err != nil {
		panic(peering_err)
	}
	return jso
}

//Writes a configuration file to disk for the client-server peering instance.
func (peering PeeringInstance) write_config_to_file(config string) {
	file_path := fmt.Sprintf("/etc/wireguard/%s.conf", peering.server_name)

	err := ioutil.WriteFile(file_path, []byte(config), 0600)
	if err != nil {
		panic(err)
	}
}
