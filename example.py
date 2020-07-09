from wireguard_servers import wireguard_servers
from wireguard_clients import wireguard_clients
from wireguard_database import Wireguard_database
from wireguard_ipam import wireguard_ipam
import ipaddress


test = Wireguard_database()
test_servers = wireguard_servers(test.db_connection, test.cursor)
test_clients = wireguard_clients(test.db_connection, test.cursor)
test_subnets = wireguard_ipam(test.db_connection, test.cursor)

print(test_servers.list_all_servers())
#Create two servers.
test_servers.create_wg_server("Wireguard01", "XXXXyyyXXXX", "192.168.0.5", "10.10.10.1")
test_servers.create_wg_server("Wireguard02", "XXXXZZyyyXXXX", "192.168.0.51", "10.10.11.1")

print(test_servers.list_all_servers())

#Create two thin clients and assign them to both servers.
test_clients.create_wg_client("client11", "Wireguard02", "ZZZZycyy2XXXX")
test_clients.create_wg_client("client11", "Wireguard01", "ZZZZycsyy2XXXX")
test_clients.create_wg_client("client12", "Wireguard01", "ZZZZy2csyy2XXXX")
test_clients.create_wg_client("client12", "Wireguard02", "ZZZZy2csvyy2XXXX")

print(test_clients.list_all_clients())

#Create subnets for both servers.
test_subnets.create_subnet("10.10.10.0/24", 20)
test_subnets.create_subnet("10.10.11.0/24", 20)

print(test_subnets.list_all_subnets())

#Assign subnets to the servers.
test_subnets.assign_subnet("10.10.10.0/24", "Wireguard01")
test_subnets.assign_subnet("10.10.11.0/24", "Wireguard02")

print(test_subnets.list_all_subnets())

#Create leases for clients.
test_subnets.create_lease("client12", "Wireguard01")
test_subnets.create_lease("client12", "Wireguard02")
test_subnets.create_lease("client11", "Wireguard01")
test_subnets.create_lease("client11", "Wireguard02")

print(test_subnets.list_assigned_ips("10.10.10.0/24"))
print(test_subnets.list_assigned_ips("10.10.10.0/24"))

#Print out required clients info for each server.
print(test_servers.retrieve_servers_client_details("Wireguard02"))
print(test_servers.retrieve_servers_client_details("Wireguard02"))