import psycopg2, ipaddress

class Wireguard_database():
    """
    Connects to, validates, and formats (if needed) a postgres database to be used by wireguard api components.

    Attributes
    ----------
    db_connection : psycopg2.extensions.connection
        The connection to the postgres database.
    db_cursor : psycopg2.extensions.cursor
        psycopg2 used for issuing commands to the database.

    Methods
    -------
    validate_database()
        Checks for a valid Postgres database that already store context.
    format_database()
        Called to create the tables required when conencting to an empty database.
    """
    def __init__(self, db_server="127.0.0.1", db_port="5432", db_database="postgres", db_user="postgres", db_password="changeme123"):
        """
        Parameters
        ----------
        db_server : str
            The location of the postgres database. (default is 127.0.0.1)
        db_port : str
            The port to connect to the database on (default is 5432)
        db_database : str
            The name of the database (default is postgres)
        db_user : str
            The user to connect to the database (default is postgres)
        db_password : str
            The password for the user connecting to the database (default is changeme123)
        """
        try:
            self.db_connection = psycopg2.connect(host = db_server, database = db_database, port = db_port, user = db_user, password = db_password)
            self.cursor = self.db_connection.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Unable to connect to database, failed with error: ", error)
        else:
            print("Debug: Connected to database.")
        if not self.validate_database():
            self.format_database()
        else:
            print("Debug: Found tables within database.")

    def validate_database(self):
        """ Performs a very basic check on the data base of existing content. 
        If any tables are found, database is assumed valid.
        """
        try:
            self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            if len(self.cursor.fetchall()) != 0:
                return True
            else:
                print("Debug: No tables exist in database, tables will be created.")
                return False
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not read from database, failed with error: ", error)

    def format_database(self):
        try:
            self.cursor.execute("""
            CREATE TABLE servers (
                serverID VARCHAR (20) PRIMARY KEY,
                public_key VARCHAR (40) UNIQUE,
                endpoint_address VARCHAR (15),
                endpoint_port INT
            );
            """)
            self.db_connection.commit()
            self.cursor.execute("""
            CREATE TABLE clients (
                clientID serial PRIMARY KEY,
                client_name VARCHAR (20),
                public_key VARCHAR (40) UNIQUE,
                serverID VARCHAR (20),
                CONSTRAINT clients_serverID_fkey FOREIGN KEY (serverID) 
                REFERENCES servers (serverID) ON DELETE CASCADE
            );
            """)
            self.db_connection.commit()
            self.cursor.execute("""
            CREATE TABLE subnets (
                subnetID serial PRIMARY KEY,
                serverID VARCHAR (20),
                allowed_ips VARCHAR,
                network_address VARCHAR (15) UNIQUE,
                network_mask INT,
                n_reserved_ips INT,
                CONSTRAINT subnets_serverID_fkey FOREIGN KEY (serverID) 
                REFERENCES servers (serverID) ON DELETE CASCADE
            );
            """)
            self.db_connection.commit()
            self.cursor.execute("""
            CREATE TABLE leases (
                leaseID serial PRIMARY KEY,
                subnetID serial,
                clientID serial UNIQUE,
                ip_address VARCHAR (15) UNIQUE,
                CONSTRAINT leases_clientID_fkey FOREIGN KEY (clientID) 
                REFERENCES clients (clientID) ON DELETE CASCADE,
                CONSTRAINT leases_subnetID_fkey FOREIGN KEY (subnetID) 
                REFERENCES subnets (subnetID) ON DELETE CASCADE
            );
            """)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not create database, failed with error: ", error)
        else:
            print("Debug: Successfully formatted database.")

    def create_server(self, server_name, network_address, network_mask, public_key, endpoint_address, endpoint_port, n_reserved_ips, allowed_ips):
        try:
            self.cursor.execute("""
            INSERT INTO servers (serverID, public_key, endpoint_address, endpoint_port) VALUES ( %s, %s, %s, %s)
            """, (server_name, public_key, endpoint_address, endpoint_port))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not add server {server_name}: ", error)
            raise Exception("Could not create server.")
        else:
            print(f"Debug: Successfully added server: {server_name}.")
        self.create_subnet(server_name, network_address, network_mask, n_reserved_ips, allowed_ips)
        return True

    def delete_server(self, server_name):
        try:
            self.cursor.execute("DELETE FROM servers WHERE servers.serverID = %s;", (server_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete server {server_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted server {server_name}.")
    
    def create_subnet(self, server_name, network_address, network_mask, n_reserved_ips, allowed_ips):
        try:
            self.cursor.execute("""
            INSERT INTO subnets (serverID, network_address, network_mask, n_reserved_ips, allowed_ips ) VALUES ( %s, %s, %s, %s, %s )
            ;""", (server_name, network_address, network_mask, n_reserved_ips, allowed_ips,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not add subnet for {server_name}: ", error)
            raise Exception("Could not create subnet.")
        else:
            print(f"Debug: Successfully added subnet: {network_address}/{network_mask}.")
            return True

    def create_client(self, client_name, server_name, public_key):
        self.delete_client_peering(client_name, server_name)
        try:
            self.cursor.execute("""
            INSERT INTO clients (client_name, public_key, serverID) VALUES ( %s, %s, %s)
            ;""", (client_name, public_key, server_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not create client: ", error)
        else:
            print(f"Debug: Successfully added client: {client_name}.")
        self.assign_lease(client_name, server_name)

    def delete_client(self, client_name):
        try:
            self.cursor.execute("DELETE FROM clients WHERE clients.client_name = %s;", (client_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete client {client_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted client {client_name}.")

    def delete_client_peering(self, client_name, server_name):
        try:
            self.cursor.execute("DELETE FROM clients WHERE clients.client_name = %s AND clients.serverID = %s;", (client_name, server_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete client-server peering of {client_name}-{server_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted client-server peer {client_name}-{server_name}.")

    def assign_lease(self, client_name, server_name):
        ip_address = self.get_next_ip(server_name)
        int_ip = self.ip_to_int(ip_address)
        try:
            self.cursor.execute("""
            INSERT INTO leases (subnetID, clientID, ip_address) VALUES (
            (SELECT subnetID FROM subnets WHERE serverID = %s),
            (SELECT clientID FROM clients WHERE client_name = %s),
            %s );""", (server_name, client_name, int_ip,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not assign lease to client {client_name}: ", error)
        else:
            print(f"Debug: Successfully added client: {client_name}.")

    def get_next_ip(self, server_name):
        try:
            self.cursor.execute("""SELECT leases.ip_address FROM subnets INNER JOIN leases ON subnets.subnetID = leases.subnetID 
            WHERE subnets.serverID = %s;""", (server_name,))
            taken_ips = self.cursor.fetchall()
            self.cursor.execute("SELECT network_address, network_mask, n_reserved_ips FROM subnets WHERE serverID = %s", (server_name,))
            network_address, network_mask, n_reserved_ips = self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve details of subnet for client {server_name}: ", error)
        subnet = ipaddress.ip_network(f"{network_address}/{network_mask}")
        
        #Set it to the first available ip if none exist.
        if len(taken_ips) == 0:
            return subnet[n_reserved_ips + 1]

        #Format query result to list of ints
        taken_ips_ints = []
        for ip in taken_ips:
            taken_ips_ints += [int(ip[0])]

        #Return first IP address not in use
        for ipaddr in subnet.hosts():
            ipaddr = ipaddress.ip_address(ipaddr)
            intaddr = int.from_bytes(ipaddr.packed, "big")
            if not intaddr in taken_ips_ints:
                return ipaddr
    
    def ip_to_int(self, ip):
        if len(str(ip)) == 0:
            raise Exception("Error: Server out of leases")
        ipaddr = ipaddress.ip_address(ip)
        intaddr = int.from_bytes(ipaddr.packed, "big")
        return intaddr

    def list_clients(self):
        response = {}
        try:
            self.cursor.execute("SELECT * FROM clients;")
            clients =  self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)
        for client in clients:
            if not(client[1] in response.keys()):
                response[client[1]] = {}
            response[client[1]][client[0]] = {"public_key": client[2], "server": client[3]}
        return response


    def list_servers(self):
        response = {}
        try:
            self.cursor.execute("SELECT * FROM servers;")
            servers = self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull server list from database: ", error)
        for server in servers:
            response[server[0]] = {"public_key": server[1], "endpoint_address": server[2], "endpoint_port": server[3]}
        return response

    def list_leases(self):
        try:
            self.cursor.execute("SELECT * FROM leases;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)

    def list_subnets(self):
        try:
            self.cursor.execute("SELECT * FROM subnets;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)

    def get_client_id(self, client_name, server_name):
        try:
            self.cursor.execute("SELECT clientID FROM clients WHERE client_name = %s AND serverID = %s;", (client_name, server_name,))
            return self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)
    
    def get_subnet_id(self, server_name):
        try:
            self.cursor.execute("SELECT subnetID FROM subnets WHERE serverID = %s;", (server_name,))
            return self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)

    def get_client_config(self, client_name, server_name):
        clientID = self.get_client_id(client_name, server_name)
        try:
            self.cursor.execute("""SELECT public_key, endpoint_address, endpoint_port 
            FROM servers WHERE serverID = %s;""", (server_name,))
            server_details = self.cursor.fetchone()
            self.cursor.execute("""SELECT subnets.allowed_ips, leases.ip_address 
            FROM subnets
            INNER JOIN leases ON leases.subnetID = subnets.subnetID
            WHERE leases.clientID = %s;""", (clientID,))
            subnet_details = self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client details from database: ", error)
        server_details = {"public_key": server_details[0], "endpoint_address": server_details[1], "endpoint_port": server_details[2]}
        subnet_details = {"allowed_ips": subnet_details[0], "lease": str(ipaddress.IPv4Address(int(subnet_details[1])))}
        response = {"server": server_details, "subnet": subnet_details}
        return response

    def get_server_config(self, server_name):
        subnetID = self.get_subnet_id(server_name)
        response = {}
        try:
            self.cursor.execute("""SELECT clients.clientID, clients.public_key, leases.ip_address 
            FROM clients
            INNER JOIN leases ON clients.clientID = leases.clientID WHERE subnetID = %s;""", (subnetID,))
            clients = self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)
            raise Exception("Could not retrieve config for server.")
        for client in clients:
            response[client[0]] = {"public_key": client[1], "ip_address": str(ipaddress.IPv4Address(int(client[2])))}
        return response