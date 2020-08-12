package apiv1

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
)

type Peer struct {
	IPAddress string `json:"ip_address"`
	Publickey string `json:"public_key"`
}

type Peers struct {
	Peers []Peer `json:"peers"`
}

type Wg_Client struct {
	Client_name string `json:"client_name"`
	Server_name string `json:"server_name"`
	Public_key  string `json:"public_key"`
}

type Wg_ip struct {
	Wg_ip string `json:"server_wg_ip"`
}

type NewServerRequest struct {
	ServerName      string `json:"server_name"`
	NetworkAddress  string `json:"network_address"`
	NetworkMask     int    `json:"network_mask"`
	PublicKey       string `json:"public_key"`
	EndpointAddress string `json:"endpoint_address"`
	EndpointPort    int    `json:"endpoint_port"`
	NReservedIps    int    `json:"n_reserved_ips"`
	AllowedIps      string `json:"allowed_ips"`
}

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

type API_Interface struct {
	API_Server_Address  string
	API_Server_Username string
	API_Server_Password string
}

func New(api_server, api_username, api_password string) API_Interface {
	api_instance := API_Interface{api_server, api_username, api_password}
	return api_instance
}

func (api_instance API_Interface) Add_client(server_name, client_name, public_key string) error {
	var client_request = Wg_Client{
		Client_name: client_name,
		Server_name: server_name,
		Public_key:  public_key,
	}
	client_request_JSON, err := json.MarshalIndent(client_request, "", "	")
	if err != nil {
		log.Print(err)
	}

	url := api_instance.API_Server_Address + "/api/v1/client/add/"
	_, status_code, request_error := api_instance.submit_api_request(http.MethodPost, url, string(client_request_JSON))
	if request_error != nil {
		return request_error
	} else {
		if status_code == 500 {
			log.Print(fmt.Sprintf("API server was not able to broker a connection to server %s.", api_instance.API_Server_Address))
			return errors.New("ApiServerError")
		} else if status_code == 400 {
			log.Print(fmt.Sprintf("Client sent bad request to server when attempting to register with server %s.", api_instance.API_Server_Address))
			return errors.New("RequestFormatError")
		} else if status_code == 401 {
			log.Print("API server rejected credentials.")
			return errors.New("Unauthorised")
		} else if status_code != 201 {
			log.Print(fmt.Sprintf("An unexpected error occured while registering with server %s.", api_instance.API_Server_Address))
			return errors.New("Unknown")
		}
		return nil
	}
}

func (api_instance API_Interface) Get_client_details(server_name, client_name string) (Peering, error) {
	url := api_instance.API_Server_Address + "/api/v1/client/config/"
	request_str := fmt.Sprintf("{\"client_name\": \"%s\", \"server_name\":\"%s\"}", client_name, server_name)
	body_bytes, status_code, request_error := api_instance.submit_api_request(http.MethodGet, url, request_str)
	if request_error != nil {
		return Peering{}, request_error
	} else if status_code == 500 {
		log.Print(fmt.Sprintf("Was unable to get peering config for connection to server %s.", api_instance.API_Server_Address))
		return Peering{}, errors.New("Failed")
	} else if status_code == 401 {
		log.Print("API server rejected credentials.")
		return Peering{}, errors.New("Unauthorised")
	} else if status_code != 200 {
		log.Print(fmt.Sprintf("An unexpected error occured while retrieving peering details with server %s.", api_instance.API_Server_Address))
		return Peering{}, errors.New("Unknown")
	}
	var peering_details Peering
	parsing_error := json.Unmarshal(body_bytes, &peering_details)
	if parsing_error != nil {
		log.Print(parsing_error)
		return Peering{}, parsing_error
	}
	return peering_details, nil
}

func (api_instance API_Interface) Add_server(request_str string) error {
	url := api_instance.API_Server_Address + "/api/v1/server/add/"
	_, status_code, request_error := api_instance.submit_api_request(http.MethodPost, url, request_str)
	if request_error != nil || status_code != 200 {
		return request_error
	}
	if status_code == 500 {
		log.Print(fmt.Sprint("API server was not able create server."))
		return errors.New("ApiServerError.")
	} else if status_code == 400 {
		log.Print(fmt.Sprint("Client sent bad request to server when attempting to register server."))
		return errors.New("RequestFormatError")
	} else if status_code == 401 {
		log.Print("API server rejected credentials.")
		return errors.New("Unauthorised")
	} else if status_code != 201 {
		log.Print(fmt.Sprint("An unexpected error occured while registering server."))
		return errors.New("Unknown")
	}
	return nil
}

func (api_instance API_Interface) Get_server_wg_ip(server_name string) (string, error) {
	url := api_instance.API_Server_Address + "/api/v1/server/wireguard_ip/"
	request_str := fmt.Sprintf("{ \"server_name\":\"%s\" }", server_name)
	body_bytes, status_code, request_error := api_instance.submit_api_request(http.MethodGet, url, request_str)
	if request_error != nil || status_code != 200 {
		return "", request_error
	}

	var jso Wg_ip
	parsing_err := json.Unmarshal(body_bytes, &jso)
	if parsing_err != nil {
		log.Print("Failed to parse json.")
		return "", parsing_err
	}
	return jso.Wg_ip, nil
}

func (api_instance API_Interface) Get_server_peers(server_name string) (Peers, error) {
	url := api_instance.API_Server_Address + "/api/v1/server/config/"
	request_str := fmt.Sprintf("{ \"server_name\":\"%s\" }", server_name)
	body_bytes, status_code, request_error := api_instance.submit_api_request(http.MethodGet, url, request_str)
	if request_error != nil || status_code != 200 {
		return Peers{}, request_error
	}
	if status_code == 500 {
		log.Print(fmt.Sprintf("API server was not able retrieve server %s config.", server_name))
		return Peers{}, errors.New("ApiServerError")
	} else if status_code == 404 {
		log.Print(fmt.Sprintf("API server could not find details for server %s.", server_name))
		return Peers{}, errors.New("RequestFormatError")
	} else if status_code == 401 {
		log.Print("API server rejected credentials.")
		return Peers{}, errors.New("Unauthorised")
	} else if status_code != 200 {
		log.Print(fmt.Sprintf("An unexpected error occured while retrieving peers for server %s.", server_name))
		return Peers{}, errors.New("Unknown")
	}

	var jso Peers
	parsing_err := json.Unmarshal(body_bytes, &jso)
	if parsing_err != nil {
		log.Print(parsing_err)
		return Peers{}, parsing_err
	}

	return jso, nil
}

func (api_instance API_Interface) Get_server_existance(server_name string) (bool, error) {
	url := api_instance.API_Server_Address + "/api/v1/server/exists/"
	request_str := fmt.Sprintf("{ \"server_name\":\"%s\" }", server_name)
	_, status_code, request_error := api_instance.submit_api_request(http.MethodGet, url, request_str)
	if request_error != nil {
		return false, request_error
	} else if status_code != 200 {
		return false, nil
	} else {
		return true, nil
	}
}

func (api_instance API_Interface) submit_api_request(http_method, url, request_str string) ([]byte, int, error) {

	req, http_error := http.NewRequest(http_method, url, bytes.NewBuffer([]byte(request_str)))
	if http_error != nil {
		log.Print("Failed to create http request.")
		return []byte(""), 418, http_error
	}
	req.Header.Set("Content-Type", "application/json;")
	req.SetBasicAuth(api_instance.API_Server_Username, api_instance.API_Server_Password)

	client := &http.Client{}
	resp, client_error := client.Do(req)
	if client_error != nil {
		log.Printf(fmt.Sprintf("Unable to connect to Wireguard api server at %s.", url), client_error)
		return []byte(""), 418, client_error
	}

	response_bytes, read_error := ioutil.ReadAll(resp.Body)
	if read_error != nil {
		log.Print("Unable to read the body of servers response.")
		return []byte(""), 418, read_error
	}

	return response_bytes, resp.StatusCode, nil

}
