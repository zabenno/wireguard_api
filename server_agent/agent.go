package main

import (
	"agent/configparser"
	"agent/peering"
)

func main() {
	var config = configparser.New("./test.yaml")
	if config.Type == "client" {
		configure_as_client(config)
	} else if config.Type == "server" {
		configure_as_server(config)
	} else {
		panic("Wrong or no type specified.")
	}
}

func configure_as_client (config configparser.Config){
	peers := initialise_peers(config)
	for index := range peers {
		peering_instance := peers[index]
		if ! peering_instance.Check_peering_existance() {
			peering_instance.Create_peer()
			peering_instance.Create_config_file()
		}
	}
}

func configure_as_server (config configparser.Config){

}

func initialise_peers (config configparser.Config) []peering.Shittyname {
	var peering_instances []peering.Shittyname
	for index := range config.PeeringList{
		var peers configparser.PeeringInstance
		peers = config.PeeringList[index]
		peering_instances= append(peering_instances, peering.New(config.ApiServer.Address, config.ApiServer.Username, config.ApiServer.Password, config.Name, peers.Server, peers.PublicKey, peers.PrivateKey))
	}
	return peering_instances
}

