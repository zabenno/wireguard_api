package wgcli

import (
	"fmt"
	"log"
	"os/exec"
)

type Wg_Cli struct {
	wg_command_path      string
	wgquick_command_path string
}

func New() (Wg_Cli, error) {
	wireguard_quick_path, wgquick_path_error := exec.LookPath("wg-quick")
	if wgquick_path_error != nil {
		log.Print("Failed to find wg-quick command.")
		return Wg_Cli{}, wgquick_path_error
	}

	wireguard_path, wg_path_error := exec.LookPath("wg")
	if wg_path_error != nil {
		log.Print("Failed to find wg command.")
		return Wg_Cli{}, wg_path_error
	}
	return Wg_Cli{wireguard_path, wireguard_quick_path}, nil
}

func (cli Wg_Cli) Create_interface(server_name string) error {
	command := exec.Command(cli.wgquick_command_path, "up", fmt.Sprintf("/etc/wireguard/%s.conf", server_name))
	_, interface_error := command.CombinedOutput()
	if interface_error != nil {
		log.Printf("Failed to bring interface up. Interface may already exist")
		return interface_error
	}
	return nil
}

//Refreshes the in memory configuration of the wireguard server.
func (cli Wg_Cli) Sync_wireguard_conf(server_name string) error {

	command := exec.Command(cli.wg_command_path, "syncconf", server_name, fmt.Sprintf("/etc/wireguard/%s.conf", server_name))
	_, wg_exec_error := command.CombinedOutput()
	if wg_exec_error != nil {
		log.Print("Failed to sync wireguards in memory configuration.")
		return wg_exec_error
	}
	return nil
}
