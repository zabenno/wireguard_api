package main

import (
	"agent/apiserver"
	"agent/configparser"
	"agent/peering"
	"log"
	"os"
	"time"
)

//Checks whether a host is configured to be a client or server then hands over to other methods.
func main() {
	configuration_path := ""
	if len(os.Args) > 1 {
		configuration_path = os.Args[1]
	} else {
		configuration_path = "/etc/wireguard_api/wireguard_api.conf"
	}
	log.SetFlags(log.Ldate | log.Ltime)
	ensure_conf_dir()
	var config = configparser.New(configuration_path)
	if config.Type == "client" {
		configure_as_client(config)
	} else if config.Type == "server" {
		configure_as_server(config)
	} else {
		log.Fatal("Wrong or no type specified within configuration file.")
	}
}

//Checks if a file exists and is not a directory
func check_dir_exists(file_path string) bool {
	info, err := os.Stat(file_path)
	if os.IsNotExist(err) {
		return false
	}
	return info.IsDir()
}

//Ensures configuration directory exists.
func ensure_conf_dir() {
	if !check_dir_exists("/etc/wireguard_api/") {
		err := os.Mkdir("/etc/wireguard_api/", 0755)
		if err != nil {
			log.Fatal("Could not create configuration directory even though it doesn't exist.")
		}
	}
}

//Creates all peering instances specified within the configuration file and creates a seperate wireguard configuration file for each peering.
//Calls initialise_peers()
func configure_as_client(config configparser.Config) {
	peers := initialise_peers(config)
	for index := range peers {
		peering_instance := peers[index]
		if !peering_instance.Check_peering_existance() {
			err := peering_instance.Create_peer()
			if err == nil {
				config_error := peering_instance.Create_config_file()
				if config_error != nil {
					log.Print("Couldn't create config file a peer.")
				}
			}
		}
	}
}

//More work to do. Currently recreates a configuration file for the server every 60 seconds and, if it finds a difference from the last created, resyncs wireguards in memory configuration.
//Calls initialise_server()
func configure_as_server(config configparser.Config) {
	current_config := ""
	server, server_error := initialise_server(config)
	if server_error != nil {
		log.Fatal("Could not create server. Aborting.")
	}
	//Register server if it doesn't exist.
	registered, registered_error := server.Server_is_registered()
	if registered_error != nil {
		log.Fatal("Could not validate server registration status.")
	}
	if !registered {
		err := server.Register_server()
		if err != nil {
			log.Fatal("Could not register with API server. Aborting.")
		}
	}

	//Initial run to bring interface up.
	pulled_config, pulled_config_error := server.Get_wgquick_config()
	if pulled_config_error != nil {
		log.Fatal("Could not pull configuration.")
	}
	update_error := server.Update_config_file(pulled_config)
	if update_error != nil {
		log.Fatal("Unable to update configuration file")
	}
	interface_error := server.Create_interface()
	if interface_error != nil {
		log.Print("Unable to Create interface.")
	}

	//Periodically check for new clients and update configuration if client list changes.
	for true {

		pulled_config, err := server.Get_config_contents()
		if pulled_config != current_config && err == nil {
			server.Update_config_file(pulled_config)
			sync_error := server.Sync_wireguard_conf()
			if sync_error != nil {
				log.Print("Unsuccesfull attempt to update configuration.")
			} else {
				current_config = pulled_config
			}
		} else if err != nil {
			log.Println("An error occured preventing a refresh of the configuration.")
		} else {
			log.Println("No change to configuration detected.")
		}
		time.Sleep(time.Duration(server.Refresh_time) * time.Second)
	}
}

//Called by configure_as_server()
//Creates a server object in localy memory.
func initialise_server(config configparser.Config) (apiserver.Server, error) {
	server, server_error := apiserver.New(config)
	if server_error != nil {
		log.Print("Failed to initialise server.")
		return apiserver.Server{}, server_error
	}
	return server, nil
}

//Called by configure_as_client()
//Creates a list of peering instances for all peering instances specified with the configuration file.
func initialise_peers(config configparser.Config) []peering.PeeringInstance {
	var peering_instances []peering.PeeringInstance
	for index := range config.PeeringList {
		var peers configparser.PeeringInstance
		peers = config.PeeringList[index]
		peering_instance, peering_error := peering.New(config.ApiServer.Address, config.ApiServer.Username, config.ApiServer.Password, config.Name, peers.Server)
		if peering_error != nil {
			log.Printf("Failed to peer to %s", peers.Server)
		} else {
			peering_instances = append(peering_instances, peering_instance)
		}
	}
	return peering_instances
}
