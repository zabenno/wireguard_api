import ipaddress, psycopg2

class wireguard_ipam():
    def __init__(self, db_connection, cursor):
        self.db_connection = db_connection
        self.cursor = cursor
    
    def create_subnet(self, cidr_range, n_reserved_ips):
        try:
            self.cursor.execute("""
            INSERT INTO subnets (cidr_range, n_reserved_ips ) VALUES ( %s, %s )
            ;""", (cidr_range, n_reserved_ips))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not add subnet: ", error)
        else:
            print(f"Debug: Successfully added subnet: {cidr_range}.")

    def delete_subnet(self, cidr_range):
        try:
            self.cursor.execute("""
            DELETE FROM subnets WHERE subnets.cidr_range =  %s;""", (cidr_range))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not delete subnet: ", error)
        else:
            print(f"Debug: Successfully deleted subnet: {cidr_range}.")

    def assign_subnet(self, cidr_range, serverID):
        try:
            self.cursor.execute("""
            UPDATE subnets SET serverID = %s WHERE subnets.cidr_range = %s
            ;""", (serverID, cidr_range))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not assign subnet to server ", error)
        else:
            print(f"Debug: Successfully assigned subnet {cidr_range} to {serverID}.")

    def create_lease(self, wg_client, wg_server):
        clientID = self.get_client_ID(wg_client, wg_server)
        wg_servers_cidr = self.get_servers_cidr(wg_server)
        next_lease_available = self.get_next_ip(wg_servers_cidr)
        ipaddr = ipaddress.ip_address(next_lease_available)
        intaddr = int.from_bytes(ipaddr.packed, "big")

        try:
            self.cursor.execute("INSERT INTO leases (cidr_range, clientID, ip_address) VALUES ( %s, %s, %s);", (wg_servers_cidr, clientID, intaddr))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not assign ip address {next_lease_available} to client {wg_client}: ", error)
        else:
            print(f"Debug: Successfully assigned ip address {ipaddr} to client {wg_client}")

    def delete_lease(self, wg_client, wg_server):
        clientID = self.get_client_ID(wg_client, wg_server)
        try:
            self.cursor.execute("""
            DELETE FROM leases WHERE leases.clientID =  %s;""", (clientID,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not delete lease: ", error)
        else:
            print(f"Debug: Successfully deleted client lease: {clientID}.")

    def get_next_ip(self, cidr_range):
        try:
            self.cursor.execute("SELECT MAX(ip_address) FROM leases WHERE leases.cidr_range = %s;", (cidr_range,))
            current_highest_ip = self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve leases for subnet {cidr_range}: ", error)
        if current_highest_ip == None:
            try:
                self.cursor.execute("SELECT n_reserved_ips FROM subnets WHERE subnets.cidr_range = %s", (cidr_range,))
                n_reserved_ips = self.cursor.fetchone()[0]
            except (Exception, psycopg2.DatabaseError) as error:
                print("Error: Failed to retrieve number of reserved ips from database: ", error)
            ip = ipaddress.ip_network(cidr_range)[n_reserved_ips] + 1
        else:
            if ipaddress.IPv4Address(current_highest_ip + 1) in ipaddress.ip_network(cidr_range):
                ip = current_highest_ip + 1 
        
        return ip

    def get_servers_cidr(self, serverID):
        try:
            self.cursor.execute("SELECT cidr_range FROM subnets WHERE subnets.serverID = %s;", (serverID,))
            return self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve subnet for {serverID}: ", error)

    def get_client_ID(self, client_name, server_name):
        try:
            self.cursor.execute("SELECT clientID FROM clients WHERE clients.serverID = %s AND clients.client_name = %s;", (server_name,client_name))
            return self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve ID for client {client_name}: ", error)

    def list_assigned_ips(self, cidr_range):
        try:
            self.cursor.execute("SELECT ip_address FROM leases WHERE leases.cidr_range = %s;", (cidr_range,))
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve leases for subnet {cidr_range}: ", error)

    def list_all_subnets(self):
        try:
            self.cursor.execute("SELECT * FROM subnets;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve subnets: ", error)