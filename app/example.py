from wireguard_db import Wireguard_database

test = Wireguard_database()

#Create servers
test.create_server("wireguard01", "192.168.2.0", 24, "SSHHUUBBWW", "192.168.2.55", 5128, 20, "192.168.2.0/32")
test.create_server("wireguard02", "192.168.1.0", 24, "SSHHUUBfBWW", "192.168.2.55", 5128, 20, "192.168.1.0/32")

#Create client to show deletion works
test.create_client("testclient1", "wireguard02", "JJIINNPkhPSS")

print(test.list_clients())

#Delete client
test.delete_client("testclient1")

print(test.list_clients())

#Create clients
test.create_client("testclient2", "wireguard01", "JJIIYYNNPPSS")
test.create_client("testclient3", "wireguard01", "JJIIYYNNPfPSS")

#Recreate client to show it works and that software is server specific
test.create_client("testclient1", "wireguard02", "JJIINNPkhPSS")

print(test.list_clients())

#Show retrieving client config works
test.get_client_config("testclient3", "wireguard01")

#Show retrieving server config works
test.get_server_config("wireguard01")