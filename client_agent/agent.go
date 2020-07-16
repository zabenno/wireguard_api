package main

import (
	"bytes"
	"net/http"
	"fmt"
	"io/ioutil"
	"encoding/json"
)

type Server struct {
	Endpoint_address string `json:"endpoint_address"`
	Endpoint_port int `json:"endpoint_port"`
	Public_key string `json:"public_key"`
}

type Subnet struct {
	Allowed_ips string `json:"allowed_ips"`
	Lease string `json:"lease"`
}

type Peering struct {
	Server Server `json:"server"`
	Subnet Subnet `json:"subnet"`
}

type Client struct {
	Client_name string `json:"client_name"`
	Server_name string `json:"server_name"`
	Public_key string `json:"public_key"`
}

func main()  {
	server := "https://wireguard_api.docker.localhost"
	client_name := "testclient00"
	server_name := "wireguard01"
	public_key := "ZZTBDDGdiiffGCassCZH"
	username := "admin"
	password := "password"

	//Create Peer
	var request_str = generate_peering_request(public_key, client_name, server_name)
	var result = submit_peering_request(server, request_str, username, password)
	fmt.Print(result, "\n")

	//Create config from create peer.
	var json_details = get_peering_details(server, client_name, server_name)
	var config = generate_conf(json_details, public_key)
	fmt.Print(config, "\n")

}

func generate_peering_request (public_key, client_name, server_name string) string {
	var client_request = Client{
		Client_name: client_name,
		Server_name: server_name,
		Public_key: public_key,
	}
	client_request_JSON, err := json.MarshalIndent(client_request, "", "	")
	if err != nil {
        panic(err)
	}
	return string(client_request_JSON)
}

func submit_peering_request(server, request_str, username, password string) string {
	url := server + "/api/v1/client/add/"
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewBuffer([]byte(request_str)))
	if err != nil {
        panic(err)
	}
	req.Header.Set("Content-Type", "application/json;")
	req.SetBasicAuth(username, password)

	client := &http.Client{}
	resp, err := client.Do(req)
    if err != nil {
        panic(err)
	}
	
	bodyText, err := ioutil.ReadAll(resp.Body)
    s := string(bodyText)
    return s
}

func generate_conf (peering_details Peering, private_key string) string {
	conf := fmt.Sprintf("[Interface]\nAddress = %s\nPrivateKey = %s\n\n[Peer]\nPublic_key = %s\nAllowedIPs = %s\nEndpoint = %s:%d",
	peering_details.Subnet.Lease, private_key, peering_details.Server.Public_key, peering_details.Subnet.Allowed_ips, 
	peering_details.Server.Endpoint_address, peering_details.Server.Endpoint_port)

	return conf
}

func get_peering_details (server, client_name, server_name string) Peering {
	url := server + "/api/v1/client/config/"
	var body = []byte(fmt.Sprintf("{\"client_name\": \"%s\", \"server_name\":\"%s\"}", client_name, server_name))
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
		panic(err)
	}
	return jso
}