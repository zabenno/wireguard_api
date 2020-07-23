package configparser

import(
    "gopkg.in/yaml.v2"
    "io/ioutil"
    "log"
)

type Server struct {
	Name			string `yaml:"name"`
	Subnet 			Subnet `yaml:"subnet"`
	PublicKey       string `yaml:"public_key"`
	PrivateKey      string `yaml:"private_key"`
	EndpointAddress string `yaml:"endpoint_address"`
	EndpointPort     string `yaml:"endpoint_port"`
}

type Subnet struct {
	NetworkAddress string  `yaml:"network_address"`
	NetworkMask    string  `yaml:"network_mask"`
	NumReservedIps int     `yaml:"num_reserved_ips"`
	AllowedIps     string  `yaml:"allowed_ips"`
}

type ApiServer struct {
	Address  string `yaml:"address"`
	Username string `yaml:"username"`
	Password string `yaml:"password"`
}

type PeeringInstance struct {
	Server     string `yaml:"server_name"`
	PublicKey  string `yaml:"public_key"`
	PrivateKey string `yaml:"private_key"`
}

type Config struct {
	Name        string      		`yaml:"name"`
	Type        string      		`yaml:"type"`
	ApiServer   ApiServer			`yaml:"api_server"`
	Server      Server				`yaml:"server,omitempty"`
	PeeringList []PeeringInstance 	`yaml:"peering_list,omitempty"`
}

func New(conf_file_path string) Config {
	configuration, err := ioutil.ReadFile(conf_file_path)
	if err != nil {
		log.Fatal(err)
	}

	var conf Config
	err = yaml.Unmarshal(configuration, &conf)
	if err != nil {
		panic(err)
	}

	return conf
}