import psycopg2

class wireguard_clients():
    """
    A class used to logically seperate wireguard client based actions from the rest of the wireguard api.
    
    Attributes
    ----------
    db_connection : psycopg2.extensions.connection
        The connection to the postgres database.
    db_cursor : psycopg2.extensions.cursor
        psycopg2 used for issuing commands to the database.

    Methods
    -------
    create_wg_client(client_name, wg_server, public_key)
        Adds a new client to a server.
    delete_wg_client(client_name)
        Completely removes a client from all servers.
    retrieve_client_config(wg_client)
        Returns all information required to configure a client.
    list_all_clients()
        Returns a list of all clients defined.
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
    
    def create_wg_client(self, client_name, wg_server, public_key):
        """
        Creates a client and associates it to a defined server.

        Parameters
        ----------
        client_name : str
            The name of the client
        wg_server : str
            The name of the server to associate the client to.
        public_key : str
            The public key of the client.
        """
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
        """
        Deletes a client and its association with all servers.

        Parameters
        ----------
        client_name : str
            The name of the client to be removed.
        """
        try:
            self.cursor.execute("DELETE FROM clients WHERE clients.client_name = %s;", (client_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete client {client_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted client {client_name}.")
    
    def retrieve_client_config(self, wg_client):
        """
        Returns all information required to configure a client for connection to its servers.

        Parameters
        ----------
        wg_client : str
            The name of the client to fetch the configuration for.

        Returns
        -------
        list
            A list of all the information required by the client.
        """
        try:
            self.cursor.execute("SELECT serverID, public_key FROM clients WHERE clients.client_name = %s;", (wg_client,))
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve configuration for client {wg_client}: ", error)
    
    def list_all_clients(self):
        """
        Lists all distinct clients

        Returns
        -------
        list
            A list of all distinct client names.
        """
        try:
            self.cursor.execute("SELECT DISTINCT client_name FROM clients;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)