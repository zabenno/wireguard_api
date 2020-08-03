package apiserver

import (
	"agent/configparser"
	"agent/keypair"
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os/exec"
)

type Client struct {
	IPAddress string `json:"ip_address"`
	Publickey string `json:"public_key"`
}

type Clients struct {
	Clients []Client `json:"peers"`
}

type Server struct {
	api_server      string
	api_username    string
	api_password    string
	server_name     string
	public_key      string
	private_key     string
	endpointaddress string
	endpointport    string
	subnet          Subnet
}

type Subnet struct {
	NetworkAddress string
	NetworkMask    string
	NumReservedIps int
	AllowedIps     string
}

type NewServerRequest struct {
	ServerName      string `json:"server_name"`
	NetworkAddress  string `json:"network_address"`
	NetworkMask     string `json:"network_mask"`
	PublicKey       string `json:"public_key"`
	EndpointAddress string `json:"endpoint_address"`
	EndpointPort    string `json:"endpoint_port"`
	NReservedIps    int    `json:"n_reserved_ips"`
	AllowedIps      string `json:"allowed_ips"`
}

//Creates a new server instance in local memory.
func New(config configparser.Config) Server {
	keypair := keypair.New(config.Server.Name)
	servers_subnet := Subnet{config.Server.Subnet.NetworkAddress, config.Server.Subnet.NetworkMask, config.Server.Subnet.NumReservedIps, config.Server.Subnet.AllowedIps}
	server := Server{config.ApiServer.Address, config.ApiServer.Username, config.ApiServer.Password, config.Server.Name, keypair.Public_key, keypair.Private_key, config.Server.EndpointAddress, config.Server.EndpointPort, servers_subnet}
	return server
}

//Submits a peering request to the wireguard_api server.
func (server Server) Register_server() {
	url := server.api_server + "/api/v1/server/add/"
	request_str := server.generate_peering_request()
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewBuffer([]byte(request_str)))
	if err != nil {
		panic(err)
	}
	req.Header.Set("Content-Type", "application/json;")
	req.SetBasicAuth(server.api_username, server.api_password)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	if resp.StatusCode != 201 {
		panic(resp.StatusCode)
	}
}

//Creates the content that will be placed in the body of the REST API call to the wireguard_api server.
func (server Server) generate_peering_request() string {
	var new_server_request = NewServerRequest{
		ServerName:      server.server_name,
		NetworkAddress:  server.subnet.NetworkAddress,
		NetworkMask:     server.subnet.NetworkMask,
		PublicKey:       server.public_key,
		EndpointAddress: server.endpointaddress,
		EndpointPort:    server.endpointport,
		NReservedIps:    server.subnet.NumReservedIps,
		AllowedIps:      server.subnet.AllowedIps,
	}
	new_server_request_JSON, err := json.MarshalIndent(new_server_request, "", "	")
	if err != nil {
		panic(err)
	}
	return string(new_server_request_JSON)
}

//Returns bool based on if the server is registered with the wireguard api or not.
func (server Server) Server_is_registered() bool {
	url := server.api_server + "/api/v1/server/list_all"
	req, err := http.NewRequest(http.MethodGet, url, bytes.NewBuffer([]byte("")))
	if err != nil {
		panic(err)
	}

	client := &http.Client{}

	req.SetBasicAuth(server.api_username, server.api_password)
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
	var jso map[string]interface{}
	peering_err := json.Unmarshal(bytes, &jso)
	if peering_err != nil {
		panic(peering_err)
	}

	//Check response for existance of server instance.
	if _, exists := jso[server.server_name]; exists {
		return true
	} else {
		return false
	}

}

//Refreshes the in memory configuration of the wireguard server.
func (server Server) Sync_wireguard_conf() {
	wireguard_path, err := exec.LookPath("wg")

	if err != nil {
		panic(err)
	} else {
		command := exec.Command(wireguard_path, "syncconf", server.server_name, fmt.Sprintf("/etc/wireguard/%s.conf", server.server_name))
		output, err := command.CombinedOutput()
		if err != nil {
			fmt.Print("\nOutput: ", string(output))
			panic(err)
		}
	}
}

//Updates the on disk configuration for the wireguard server.
func (server Server) Update_config_file(config string) {
	file_path := fmt.Sprintf("/etc/wireguard/%s.conf", server.server_name)

	err := ioutil.WriteFile(file_path, []byte(config), 0600)
	if err != nil {
		panic(err)
	}
}

//Creates the contents for the peers section of the server configuration file for all clients assigned to it.
func (server Server) Get_config_contents() string {
	response := server.get_interface_config()
	peers := server.get_peers()
	for index := range peers.Clients {
		response += fmt.Sprintf("[Peer]\nPublicKey = %s\nAllowedIPs = %s/32\n\n", peers.Clients[index].Publickey, peers.Clients[index].IPAddress)
	}
	return response
}

//Creates the contents for the interface section of the wireguard server configuration
func (server Server) get_interface_config() string {
	response := "[Interface]\n"
	response += fmt.Sprintf("Address = %s/%s\n", server.subnet.NetworkAddress, server.subnet.NetworkMask)
	response += fmt.Sprintf("ListenPort = %s\n", server.endpointport)
	response += fmt.Sprintf("PrivateKey = %s\n\n", server.private_key)
	return response
}

//Retrieves the required information for the server to configure itself to establish connections to all assigned clients.
func (server Server) get_peers() Clients {
	url := server.api_server + "/api/v1/server/config/"
	var body = []byte(fmt.Sprintf("{ \"server_name\":\"%s\" }", server.server_name))
	req, err := http.NewRequest(http.MethodGet, url, bytes.NewBuffer(body))
	if err != nil {
		panic(err)
	}

	client := &http.Client{}

	req.SetBasicAuth(server.api_username, server.api_password)
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
	var jso Clients
	peering_err := json.Unmarshal(bytes, &jso)
	if peering_err != nil {
		panic(peering_err)
	}

	return jso
}
