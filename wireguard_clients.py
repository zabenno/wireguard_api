import psycopg2

class wireguard_clients():
    def __init__(self, database, cursor):
        self.db_connection = database
        self.cursor = cursor
    
    def create_wg_client(self, client_name, wg_server, public_key):
        try:
            self.cursor.execute("""
            INSERT INTO clients (client_name, public_key, serverID) VALUES ( %s, %s, %s)
            ;""", (client_name, public_key, wg_server,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not add wg_client: ", error)
        else:
            print(f"Debug: Successfully added wg_client: {client_name}.")
    
    def delete_wg_client(self, client_name):
        try:
            self.cursor.execute("DELETE FROM clients WHERE clients.client_name = %s;", (client_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete client {client_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted client {client_name}.")
    
    def retrieve_client_config(self, wg_client):
        try:
            self.cursor.execute("SELECT serverID, public_key FROM clients WHERE clients.client_name = %s;", (wg_client,))
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve configuration for client {wg_client}: ", error)
    
    def list_all_clients(self):
        try:
            self.cursor.execute("SELECT DISTINCT client_name FROM clients;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)