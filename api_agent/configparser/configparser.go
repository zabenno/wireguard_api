package configparser

import (
	"io/ioutil"
	"log"

	"gopkg.in/yaml.v2"
)

type Server struct {
	Name            string `yaml:"name"`
	Subnet          Subnet `yaml:"subnet"`
	EndpointAddress string `yaml:"endpoint_address"`
	EndpointPort    int    `yaml:"endpoint_port"`
}

type Subnet struct {
	NetworkAddress string `yaml:"network_address"`
	NetworkMask    int    `yaml:"network_mask"`
	NumReservedIps int    `yaml:"num_reserved_ips"`
	AllowedIps     string `yaml:"allowed_ips"`
}

type ApiServer struct {
	Address  string `yaml:"address"`
	Username string `yaml:"username"`
	Password string `yaml:"password"`
}

type PeeringInstance struct {
	Server string `yaml:"server_name"`
}

type Config struct {
	Name        string            `yaml:"name"`
	Type        string            `yaml:"type"`
	ApiServer   ApiServer         `yaml:"api_server"`
	Server      Server            `yaml:"server,omitempty"`
	PeeringList []PeeringInstance `yaml:"peering_list,omitempty"`
}

//Creates a configuration object from the file path given.
func New(conf_file_path string) Config {
	configuration, read_error := ioutil.ReadFile(conf_file_path)
	if read_error != nil {
		log.Fatalf("Failed to read configuration file with error: %s", read_error)
	}

	var conf Config
	parser_error := yaml.Unmarshal(configuration, &conf)
	if parser_error != nil {
		log.Fatalf("Failed to parse configuration file with error: %s", parser_error)
	}

	return conf
}
