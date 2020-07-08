import psycopg2

class wireguard_servers():
    def __init__(self, database, cursor):
        self.db_connection = database
        self.cursor = cursor
    
    def create_wg_server(self, server_name, public_key, ip_address, wg_ip_range, wg_ip_address):
        try:
            self.cursor.execute("""
            INSERT INTO wg_servers (serverID, public_key, ip_address, wg_ip_range, wg_ip_address) VALUES ( %s, %s, %s, %s, %s)
            """, (server_name, public_key, ip_address, wg_ip_range, wg_ip_address))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not add wg_server: ", error)
        else:
            print(f"Debug: Successfully added wg_server: {server_name}.")
    
    def delete_wg_server(self, server_name):
        try:
            self.cursor.execute("DELETE FROM wg_servers WHERE wg_servers.serverID = %s;", (server_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete server {server_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted server {server_name}.")

    def list_servers_clients(self, wg_server):
        try:
            self.cursor.execute("SELECT client_name FROM clients WHERE clients.serverID = %s;", (wg_server,))
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve clients for {wg_server}: ", error)
    
    def list_all_servers(self):
        try:
            self.cursor.execute("SELECT serverID FROM wg_servers;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull server list from database: ", error)
    
    def retrieve_servers_client_details(self, wg_server):
        try:
            self.cursor.execute("SELECT client_name, public_key, ip_address FROM clients WHERE clients.serverID = %s;", (wg_server,))
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve clients for {wg_server}: ", error)