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

func main()  {
	url := "https://wireguard_api.docker.localhost/api/v1/client/config/"
	client_name := "testclient1"
	server_name := "wireguard02"
	var json_details = get_peering_details(url, client_name, server_name)

	var config = generate_conf(json_details, "ZZTTBBDDGGCC")

	fmt.Print(config)
	
}

func generate_conf (peering_details Peering, private_key string) string {
	conf := fmt.Sprintf("[Interface]\nAddress = %s\nPrivateKey = %s\n\n[Peer]\nPublic_key = %s\nAllowedIPs = %s\nEndpoint = %s:%d",
	peering_details.Subnet.Lease, private_key, peering_details.Server.Public_key, peering_details.Subnet.Allowed_ips, 
	peering_details.Server.Endpoint_address, peering_details.Server.Endpoint_port)

	return conf
}

func get_peering_details (url, client_name, server_name string) Peering {
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

	bodyStr := string(bodyBytes)

	bytes := []byte(bodyStr)
	var jso Peering
	peering_err := json.Unmarshal(bytes, &jso)
	if peering_err != nil {
		panic(err)
	}
	return jso
}