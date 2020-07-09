import psycopg2, ipaddress

class wireguard_servers():
    """
    A class used to logically seperate wireguard server based actions from the rest of the wireguard api.
    
    Attributes
    ----------
    db_connection : psycopg2.extensions.connection
        The connection to the postgres database.
    db_cursor : psycopg2.extensions.cursor
        psycopg2 used for issuing commands to the database.

    Methods
    -------
    create_wg_server(server_name, public_key, ip_address, wg_ip_address)
        Adds a new wireguard server to the database.
    delete_wg_server(erver_name)
        Deletes a wireguard server from the database. (Requires no dependents)
    list_servers_clients(wg_server)
        Lists all clients by client name associated with a server.
    list_all_servers()
        Lists all Servers by ID
    retrieve_servers_client_details(wg_server)
        Lists details required for the server to configured to serve all clients.
    """
    def __init__(self, database, cursor):
        """
        Parameters
        ----------
        db_connection : psycopg2.extensions.connection
            The connection to the postgres database.
        db_cursor : psycopg2.extensions.cursor
            psycopg2 used for issuing commands to the database.
        """
        self.db_connection = database
        self.cursor = cursor
    
    def create_wg_server(self, server_name, public_key, ip_address, wg_ip_address):
        """
        Creates a wireguard server definition to attach subnets and clients to.

        Parameters
        ----------
        server_name : str
            The name being given to the server.
        public_key : str
            The wireguard public key of the server.
        ip_address : str
            The ip address to connect to the wireguard server.
        wg_ip_address : str
            The ip address used during the wireguard session.
        """
        try:
            self.cursor.execute("""
            INSERT INTO wg_servers (serverID, public_key, ip_address, wg_ip_address) VALUES ( %s, %s, %s, %s)
            """, (server_name, public_key, ip_address, wg_ip_address,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not add wg_server: ", error)
        else:
            print(f"Debug: Successfully added wg_server: {server_name}.")
    
    def delete_wg_server(self, server_name):
        """
        Deletes a wireguard server definition via its name. (Requires all references to be removed)

        Parameters
        ----------
        server_name : str
            The name given to the server.

        Returns
        -------
        None
        """
        try:
            self.cursor.execute("DELETE FROM wg_servers WHERE wg_servers.serverID = %s;", (server_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete server {server_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted server {server_name}.")

    def list_servers_clients(self, wg_server):
        """
        Returns a list of all clients associated with the specified server.

        Parameters
        ----------
        wg_server : str
            The server to pull client list from.
        
        Returns
        -------
        list
            a list of strings of client names associated with the server.
        """
        try:
            self.cursor.execute("SELECT client_name FROM clients WHERE clients.serverID = %s;", (wg_server,))
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve clients for {wg_server}: ", error)
    
    def list_all_servers(self):
        """
        Returns a list of all defined wireguard servers.

        Returns
        -------
        list
            a list of strings of all servers defined.
        """
        try:
            self.cursor.execute("SELECT serverID FROM wg_servers;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull server list from database: ", error)
    
    def retrieve_servers_client_details(self, wg_server):
        """
        Returns all information necessary for a server to configure itself for its defined clients.

        Parameters
        ----------
        wg_server
            The server to pull back details for.

        Returns
        -------
        dict
            A dictionary of a list of details of each client being served by the server. 
        """
        parsed_conf = {}
        try:
            self.cursor.execute("SELECT clients.client_name, clients.public_key, leases.ip_address FROM leases INNER JOIN clients ON clients.clientID = leases.clientID WHERE clients.serverID = %s;", (wg_server,))
            clients_conf = self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve clients for {wg_server}: ", error)
        for client in clients_conf:
            parsed_ip = str(ipaddress.ip_address(client[2]))
            parsed_conf[client[0]] = [client[1], parsed_ip]
        return parsed_conf