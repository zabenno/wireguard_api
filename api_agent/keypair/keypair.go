package keypair

import (
	"os/exec"
	"io/ioutil"
	"strings"
	"fmt"
	"os"
)

type Keypair struct {
	Public_key string
	Private_key string
}

func New(keypair_name string) Keypair{
	keypair := Keypair{}
	if check_for_keypair(keypair_name){
		keypair.Private_key = read_file(fmt.Sprintf("/etc/wireguard_api/.%s.priv", keypair_name))
		keypair.Public_key = read_file(fmt.Sprintf("/etc/wireguard_api/%s.pub", keypair_name))
	} else {
		keypair = keypair.create_key_pair(keypair_name)
	}
	return keypair
}



//Reads file and returns string
func read_file (file_path string) string {
	key, err := ioutil.ReadFile(file_path)
	if err != nil {
		panic(err)
	}
	return string(key)
}

//Checks if both keys in a keypair exist.
func check_for_keypair (keypair_name string) bool {
	if check_file_exists(fmt.Sprintf("/etc/wireguard_api/.%s.priv", keypair_name)){
		if check_file_exists(fmt.Sprintf("/etc/wireguard_api/%s.pub", keypair_name)){
			return true
		}
	}
	return false
}

//Checks if a file exists and is not a directory
func check_file_exists (keypair_name string) bool {
	info, err := os.Stat(keypair_name)
    if os.IsNotExist(err) {
        return false
    }
    return !info.IsDir()
}

//Creates the key pair for a peering instance.
func (keypair Keypair) create_key_pair (keypair_name string) Keypair {
	wireguard_path, err := exec.LookPath("wg")
	private_key, priv_err := exec.Command(wireguard_path, "genkey").Output()
	if err != nil {
		panic(priv_err)
	}

	keypair.Private_key = strings.TrimSpace(string(private_key))

	public_key, pub_err := exec.Command("bash", "-c", fmt.Sprintf("echo %s | wg pubkey", keypair.Private_key)).Output()
	if err != nil {
		panic(pub_err)
	}

	keypair.Public_key = strings.TrimSpace(string(public_key))
	
	keypair.save_key_pair(keypair_name)
	return keypair
}

//writes keys to files.
func (keypair Keypair) save_key_pair (keypair_name string) {
	file_path := fmt.Sprintf("/etc/wireguard_api/.%s.priv", keypair_name)

	priv_err := ioutil.WriteFile(file_path, []byte(keypair.Private_key), 0600)
	if priv_err != nil {
		panic(priv_err)
	}

	filep_path := fmt.Sprintf("/etc/wireguard_api/%s.pub", keypair_name)

	pub_err := ioutil.WriteFile(filep_path, []byte(keypair.Public_key), 0600)
	if pub_err != nil {
		panic(pub_err)
	}
}