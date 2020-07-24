package main

import (
	"agent/configparser"
	"agent/peering"
	"agent/apiserver"
	"time"
)

//Checks whether a host is configured to be a client or server then hands over to other methods.
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

//Creates all peering instances specified within the configuration file and creates a seperate wireguard configuration file for each peering.
//Calls initialise_peers()
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

//More work to do. Currently recreates a configuration file for the server every 60 seconds and, if it finds a difference from the last created, resyncs wireguards in memory configuration.
//Calls initialise_server()
func configure_as_server (config configparser.Config){
	current_config := ""
	server := initialise_server(config)
	//Register server if it doesn't exist.
	if ! server.Server_is_registered(){
		server.Register_server()
	}
	//Periodically check for new clients and update configuration if client list changes.
	for true {
		
		pulled_config := server.Get_config_contents()
		if pulled_config != current_config{
			server.Update_config_file(pulled_config)
			server.Sync_wireguard_conf()
			current_config = pulled_config
		}
		time.Sleep(60 * time.Second)
	}
}

//Called by configure_as_server()
//Creates a server object in localy memory.
func initialise_server (config configparser.Config) apiserver.Server {
	var server apiserver.Server
	server = apiserver.New(config)
	return server
}

//Called by configure_as_client()
//Creates a list of peering instances for all peering instances specified with the configuration file.
func initialise_peers (config configparser.Config) []peering.PeeringInstance {
	var peering_instances []peering.PeeringInstance
	for index := range config.PeeringList{
		var peers configparser.PeeringInstance
		peers = config.PeeringList[index]
		peering_instances= append(peering_instances, peering.New(config.ApiServer.Address, config.ApiServer.Username, config.ApiServer.Password, config.Name, peers.Server, peers.PublicKey, peers.PrivateKey))
	}
	return peering_instances
}

