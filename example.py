from wireguard_servers import wireguard_servers
from wireguard_clients import wireguard_clients
from wireguard_database import Wireguard_database

test = Wireguard_database()
test_servers = wireguard_servers(test.db_connection, test.cursor)
test_clients = wireguard_clients(test.db_connection, test.cursor)
print(test_servers.list_all_servers())
test_servers.create_wg_server("Wireguard02", "XXXXZZyyyXXXX", "192.168.0.51", "10.10.11.0/24", "10.10.11.1")
print(test_servers.list_all_servers())
test_clients.create_wg_client("client11", "Wireguard02", "ZZZZycyy2XXXX", "10.10.10.13")
print(test_clients.retrieve_client_config("client11"))
print(test_clients.list_all_clients())
print(test_servers.list_servers_clients("Wireguard02"))
test_clients.delete_wg_client("client11")
print(test_servers.list_servers_clients("Wireguard02"))
test_servers.delete_wg_server("Wireguard02")
print(test_clients.list_all_clients())