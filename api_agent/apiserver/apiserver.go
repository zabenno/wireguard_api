package apiserver

import (
	"agent/configparser"
	"agent/keypair"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
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

type Wg_ip struct {
	Wg_ip string `json:"server_wg_ip"`
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
func (server Server) Register_server() error {
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
		log.Printf(fmt.Sprintf("Unable to connect to Wireguard api server at %s.", url), err)
	}

	if resp.StatusCode == 500 {
		log.Print(fmt.Sprintf("API server was not able create server %s.", server.server_name))
		return errors.New("ApiServerError.")
	} else if resp.StatusCode == 400 {
		log.Print(fmt.Sprintf("Client sent bad request to server when attempting to register server %s.", server.server_name))
		return errors.New("RequestFormatError")
	} else if resp.StatusCode == 401 {
		log.Print("API server rejected credentials.")
		return errors.New("Unauthorised")
	} else if resp.StatusCode != 201 {
		log.Print(fmt.Sprintf("An unexpected error occured while registering server %s.", server.server_name))
		return errors.New("Unknown")
	}

	return nil
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
		log.Printf(fmt.Sprintf("Unable to connect to Wireguard api server at %s.", url), err)
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

func (server Server) Create_interface() {
	wireguard_quick_path, err := exec.LookPath("wg-quick")

	if err != nil {
		panic(err)
	} else {
		command := exec.Command(wireguard_quick_path, "up", fmt.Sprintf("/etc/wireguard/%s.conf", server.server_name))
		_, err := command.CombinedOutput()
		if err != nil {
			log.Printf("Failed to bring interface up with error: %s", err)
		}
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

//Creates the contents for the configuration file to be used by `wg syncconf`
func (server Server) Get_config_contents() (string, error) {
	response := server.get_interface_config()
	peers, err := server.get_peers()
	if err != nil {
		return "", err
	}
	for index := range peers.Clients {
		response += fmt.Sprintf("[Peer]\nPublicKey = %s\nAllowedIPs = %s/32\n\n", peers.Clients[index].Publickey, peers.Clients[index].IPAddress)
	}
	return response, nil
}

//Creates the contents for the interface section of the wireguard server configuration
func (server Server) get_interface_config() string {
	response := "[Interface]\n"
	response += fmt.Sprintf("PrivateKey = %s\n", server.private_key)
	response += fmt.Sprintf("ListenPort = %s\n", server.endpointport)
	return response
}

//Creates the wireguard configuration file for wg-quick to work.
func (server Server) Get_wgquick_config() string {
	response := server.get_interface_config()
	response += fmt.Sprintf("Address = %s/%s\n", server.get_wg_ip(), server.subnet.NetworkMask)
	return response
}

//Fetches the IP address used by the wireguard interface.
func (server Server) get_wg_ip() string {
	url := server.api_server + "/api/v1/server/wireguard_ip/"
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
		log.Printf(fmt.Sprintf("Unable to connect to Wireguard api server at %s.", url), err)
	}

	bodyBytes, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	bodyStr := string(bodyBytes)

	bytes := []byte(bodyStr)
	var jso Wg_ip
	peering_err := json.Unmarshal(bytes, &jso)
	if peering_err != nil {
		panic(peering_err)
	}
	return jso.Wg_ip
}

//Retrieves the required information for the server to configure itself to establish connections to all assigned clients.
func (server Server) get_peers() (Clients, error) {
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
		log.Printf(fmt.Sprintf("Unable to connect to Wireguard api server at %s.", url), err)
	}

	if resp.StatusCode == 500 {
		log.Print(fmt.Sprintf("API server was not able retrieve server %s config.", server.server_name))
		return Clients{}, errors.New("ApiServerError")
	} else if resp.StatusCode == 404 {
		log.Print(fmt.Sprintf("API server could not find details for server %s.", server.server_name))
		return Clients{}, errors.New("RequestFormatError")
	} else if resp.StatusCode == 401 {
		log.Print("API server rejected credentials.")
		return Clients{}, errors.New("Unauthorised")
	} else if resp.StatusCode != 200 {
		log.Print(fmt.Sprintf("An unexpected error occured while retrieving peers for server %s.", server.server_name))
		return Clients{}, errors.New("Unknown")
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

	return jso, nil
}
