package main

import (
	"agent/configparser"
	"agent/peering"
	"agent/apiserver"
	"fmt"
	"time"
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
	current_config := ""
	server := initialise_server(config)
	for true {
		
		pulled_config := server.Get_config_contents()
		if pulled_config != current_config{
			fmt.Print("Different")
			server.Update_config_file(pulled_config)
			server.Sync_wireguard_conf()
			current_config = pulled_config
		} else {
			fmt.Print("same")
		}
		time.Sleep(60 * time.Second)
	}
	fmt.Print(server.Get_config_contents())
}

func initialise_server (config configparser.Config) apiserver.Server {
	var server apiserver.Server
	server = apiserver.New(config)
	return server
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

