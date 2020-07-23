package apiserver

import(
	"bytes"
	"net/http"
	"fmt"
	"io/ioutil"
	"encoding/json"
	"agent/configparser"
)

type Client struct{
	IPAddress string `json:"ip_address"`
	Publickey string `json:"public_key"`
}

type Clients struct{
	Clients []Client `json:"peers"`
}

type Server struct{
	api_server string
	api_username string
	api_password string
	server_name string
	public_key string
	private_key string
	endpointaddress string
	endpointport string
	subnet Subnet
}

type Subnet struct {
	NetworkAddress string
	NetworkMask string
	NumReservedIps int
	AllowedIps string
}

func New(config configparser.Config) Server {
	servers_subnet := Subnet{config.Server.Subnet.NetworkAddress, config.Server.Subnet.NetworkMask, config.Server.Subnet.NumReservedIps, config.Server.Subnet.AllowedIps}
	server := Server{config.ApiServer.Address, config.ApiServer.Username, config.ApiServer.Password, config.Server.Name, config.Server.PublicKey, config.Server.PrivateKey, config.Server.EndpointAddress, config.Server.EndpointPort, servers_subnet}
	return server
}

func (server Server) Get_config_contents () string {
	response := server.get_interface_config()
	peers := server.get_peers()
	for index := range peers.Clients {
		response += fmt.Sprintf("[Peer]\nPublicKey = %s\nAllowedIPs = %s/32\n\n", peers.Clients[index].Publickey, peers.Clients[index].IPAddress)
	}
	return response
}

func (server Server) get_interface_config () string {
	response := "[Interface]\n"
	response += fmt.Sprintf("Address = %s\n", server.endpointaddress )
	response += fmt.Sprintf("ListenPort = %s\n", server.endpointport)
	response += fmt.Sprintf("PrivateKey = %s\n\n", server.private_key)
	return response
}

func (server Server) get_peers () Clients {
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