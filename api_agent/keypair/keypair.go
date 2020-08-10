package keypair

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"strings"
)

type Keypair struct {
	Public_key  string
	Private_key string
}

func New(keypair_name string) (Keypair, error) {
	if check_for_keypair(keypair_name) {
		private_key, private_key_error := read_file(fmt.Sprintf("/etc/wireguard_api/.%s.priv", keypair_name))
		public_key, public_key_error := read_file(fmt.Sprintf("/etc/wireguard_api/%s.pub", keypair_name))

		if public_key_error != nil {
			return Keypair{}, private_key_error
		} else if public_key_error != nil {
			return Keypair{}, public_key_error
		} else {
			keypair := Keypair{}
			keypair.Private_key = private_key
			keypair.Public_key = public_key
			return keypair, nil
		}
	} else {
		keypair := Keypair{}
		keypair, keypair_error := keypair.create_key_pair(keypair_name)
		if keypair_error != nil {
			return Keypair{}, keypair_error
		}
		return keypair, nil
	}
}

//Reads file and returns string
func read_file(file_path string) (string, error) {
	key, read_error := ioutil.ReadFile(file_path)
	if read_error != nil {
		log.Printf("Was unable to read file at: %s. Failed with error: %s", file_path, read_error)
		return "", read_error
	}
	return string(key), nil
}

//Checks if both keys in a keypair exist.
func check_for_keypair(keypair_name string) bool {
	if check_file_exists(fmt.Sprintf("/etc/wireguard_api/.%s.priv", keypair_name)) {
		if check_file_exists(fmt.Sprintf("/etc/wireguard_api/%s.pub", keypair_name)) {
			return true
		}
	}
	return false
}

//Checks if a file exists and is not a directory
func check_file_exists(keypair_name string) bool {
	info, err := os.Stat(keypair_name)
	if os.IsNotExist(err) {
		return false
	}
	return !info.IsDir()
}

//Creates the key pair for a peering instance.
func (keypair Keypair) create_key_pair(keypair_name string) (Keypair, error) {
	wireguard_path, exec_err := exec.LookPath("wg")
	if exec_err != nil {
		log.Fatal("wg command not found.")
		return Keypair{}, exec_err
	}

	private_key, priv_err := exec.Command(wireguard_path, "genkey").Output()
	if priv_err != nil {
		log.Fatalf("Failed to generate private key with error: %s", priv_err)
		return Keypair{}, priv_err
	}

	keypair.Private_key = strings.TrimSpace(string(private_key))

	public_key, pub_err := exec.Command("bash", "-c", fmt.Sprintf("echo %s | wg pubkey", keypair.Private_key)).Output()
	if pub_err != nil {
		log.Fatalf("Failed to generate public key with error: %s", pub_err)
		return Keypair{}, pub_err
	}

	keypair.Public_key = strings.TrimSpace(string(public_key))

	save_error := keypair.save_key_pair(keypair_name)
	if save_error != nil {
		return Keypair{}, save_error
	}
	return keypair, nil
}

//writes keys to files.
func (keypair Keypair) save_key_pair(keypair_name string) error {
	file_path := fmt.Sprintf("/etc/wireguard_api/.%s.priv", keypair_name)

	priv_err := ioutil.WriteFile(file_path, []byte(keypair.Private_key), 0600)
	if priv_err != nil {
		log.Printf("Writing private key to file failed with error: %s", priv_err)
		return priv_err
	}

	filep_path := fmt.Sprintf("/etc/wireguard_api/%s.pub", keypair_name)

	pub_err := ioutil.WriteFile(filep_path, []byte(keypair.Public_key), 0600)
	if pub_err != nil {
		log.Printf("Writing public key to file failed with error: %s", pub_err)
		return pub_err
	}

	return nil
}
