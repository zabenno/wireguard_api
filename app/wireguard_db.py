import psycopg2, ipaddress, re, logging

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
    create_server()
        Adds a new server instance to the database.
    delete_server()
        Ensures there is no server instance of the given name.
    create_subnet()
        Adds a subnet to the database referencing a server.
    create_client()
        Ensures a client-server peering exists with the given parameters.
    delete_client()
        Removes all instances from the database where the client name is referenced.
    delete_client_peering()
        Ensures a client is not referenced by a server.
    assign_lease()
        Assigns an IP Address to be used by the client when connecting to the server.
    get_next_ip()
        Finds the next IP available for a specific server.
    ip_to_int()
        Creates an interger that can be converted back IPv4Address object later.
    list_clients()
        Lists all clients currently in the database.
    list_servers()
        Lists all servers in the database.
    list_leases()
        Lists all leases currently in the database.
    list_subnets()
        Lists all subnets currently in the database.
    get_client_id()
        Retrieves the ID of a client-server peering.
    get_subnet_id()
        Retrieves the ID of a subnet in use by a server.
    get_client_config()
        Retrieves all non-sensitive details required to configure a client.
    get_server_config()
        Retrieves all non-sensitive details required to configure a server.
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
        logging.basicConfig(level=logging.DEBUG)
        try:
            self.db_connection = psycopg2.connect(host = db_server, database = db_database, port = db_port, user = db_user, password = db_password)
            self.cursor = self.db_connection.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.fatal(f"Unable to connect to database, failed with error: %s", error)
            self.db_connection = None
        else:
            logging.debug("Connected to database.")

        if self.db_connection == None:
            raise Exception("Unreachable")

        if not self.validate_database():
            if not self.format_database():
                logging.fatal("Failed to format database.")
                raise Exception("Corrupt")
        else:
            logging.debug("Found tables within database.")

    def validate_database(self):
        """ Performs a very basic check on the data base of existing content. 
        If any tables are found, database is assumed valid.
        """
        try:
            self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            if len(self.cursor.fetchall()) != 0:
                return True
            else:
                logging.debug("No tables exist in database, tables will be created.")
                return False
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not read from database, failed with error: %s", error)
            return False

    def format_database(self):
        try:
            self.cursor.execute("""
            CREATE TABLE servers (
                serverID VARCHAR (20) PRIMARY KEY,
                public_key VARCHAR (45) UNIQUE,
                endpoint_address VARCHAR,
                endpoint_port INT
            );
            """)
            self.db_connection.commit()
            self.cursor.execute("""
            CREATE TABLE clients (
                clientID serial PRIMARY KEY,
                client_name VARCHAR (20),
                public_key VARCHAR (45) UNIQUE,
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
                server_ip VARCHAR (15) UNIQUE,
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
                ip_address VARCHAR (18) UNIQUE,
                CONSTRAINT leases_clientID_fkey FOREIGN KEY (clientID) 
                REFERENCES clients (clientID) ON DELETE CASCADE,
                CONSTRAINT leases_subnetID_fkey FOREIGN KEY (subnetID) 
                REFERENCES subnets (subnetID) ON DELETE CASCADE
            );
            """)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not create database, failed with error: %s", error)
            return False
        else:
            logging.debug("Successfully formatted database.")
            return True

    def create_server(self, server_name, network_address, network_mask, public_key, endpoint_address, endpoint_port, n_reserved_ips, allowed_ips):
        """
        This method creates a wireguard server that will be ready to have clients added to it upon the completion of this method.
        To achieve this create_subnet() is called from within this method, passing through the relevant parmaters.
        Returns: HTTP Code representing result.
        """
        sql_query = "INSERT INTO servers (serverID, public_key, endpoint_address, endpoint_port) VALUES ( %s, %s, %s, %s);"
        sql_data = (server_name, public_key, endpoint_address, endpoint_port)

        if not self.validate_ip(network_address):
            logging.error(f"Could not add server {server_name}: {network_address} not a valid IP Address.")
            return 400
        if not self.validate_network_mask(network_mask):
            logging.error(f"Could not add server {server_name}: {network_mask} not a valid network mask.")
            return 400
        if not self.validate_wg_key(public_key):
            logging.error(f"Could not add server {server_name}: Public key value \"{public_key}\" invalid.")
            return 400
        if not self.validate_ip(endpoint_address):
            logging.error(f"Could not add server {server_name}: {endpoint_address} not a valid IP Address.")
            return 400
        if not self.validate_port(endpoint_port):
            logging.error(f"Could not add server {server_name}: {endpoint_port} not a valid port number.")
            return 400
        

        try:
            self.cursor.execute(sql_query, sql_data)
            self.db_connection.commit()
            if not self.create_subnet(server_name, network_address, network_mask, n_reserved_ips, allowed_ips):
                self.delete_server(server_name)
                return 500
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not add server {server_name}: %s", error)
            return 500
        else:
            logging.debug(f"Successfully added server: {server_name}.")
            return 201

    def delete_server(self, server_name):
        """
        This method removes all rows within the database that reference this server. This includes any subnet, clients, and leases assigned to it.
        """
        sql_query = "DELETE FROM servers WHERE servers.serverID = %s;"
        sql_data = (server_name,)

        try:
            self.cursor.execute(sql_query, sql_data)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not delete server {server_name}: %s", error)
            return 500
        else:
            logging.debug(f"Succesfully deleted server {server_name}.")
            return 200
    
    def create_subnet(self, server_name, network_address, network_mask, n_reserved_ips, allowed_ips):
        """
        This method creates a subnet and assigns it to an existing server.
        This method should never be called directly as it is called from within the create_server() method.
        """
        sql_query = "INSERT INTO subnets (serverID, server_ip, network_address, network_mask, n_reserved_ips, allowed_ips ) VALUES ( %s, %s, %s, %s, %s, %s );"
        
        try:
            server_ip = str(ipaddress.IPv4Network(network_address + "/" + str(network_mask))[1])
            sql_data = (server_name, server_ip, network_address, network_mask, n_reserved_ips, allowed_ips,)

            logging.debug(server_ip)
            self.cursor.execute(sql_query, sql_data)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not add subnet for {server_name}: %s", error)
            return False
        else:
            logging.debug(f"Successfully added subnet: {network_address}/{network_mask}.")
            return True

    def create_client(self, client_name, server_name, public_key):
        """
        This method creates a client-server peering that will be ready to connect upon the server refreshing its configuration.
        In the case a peering already exists, this method will overwrite the old peering.
        This method calls assign_lease() to allow for the client to connect to the server.
        Returns: HTTP Code representing result.
        """
        if not self.validate_wg_key(public_key):
            logging.error(f"Could not create peering {client_name}-{server_name}: Public key value \"{public_key}\" invalid.")
            return 400
        if not self.check_server_exists(server_name):
            logging.error(f"Could not create peering {client_name}-{server_name}: server does not exist.")
            return 404

        sql_query = "INSERT INTO clients (client_name, public_key, serverID) VALUES ( %s, %s, %s);"
        sql_data = (client_name, public_key, server_name,)

        try:
            self.delete_client_peering(client_name, server_name)
            self.cursor.execute(sql_query, sql_data)
            self.db_connection.commit()
            if not self.assign_lease(client_name, server_name):
                logging.error(f"Failed to get a lease for {client_name}.")
                self.delete_client_peering(client_name, server_name)
                return 500
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not create peering {client_name}-{server_name}: %s", error)
            return 500
        else:
            logging.debug(f"Successfully added peering: {client_name}-{server_name}.")
            return 201
        

    def delete_client(self, client_name):
        """
        This method deletes all references to a specified client name. This will free any leases the client may have had and remove it from all servers.
        """

        sql_query = "DELETE FROM clients WHERE clients.client_name = %s;"
        sql_data = (client_name,)

        try:
            self.cursor.execute(sql_query, sql_data)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not delete client {client_name}.: %s", error)
            return 500
        else:
            logging.debug(f"Succesfully deleted client {client_name}.")
            return 200

    def delete_client_peering(self, client_name, server_name):
        """
        This method deletes a single instance of peering between a specified client and server.
        This will free the lease that was used by the client to connect to the server.
        """

        sql_query = "DELETE FROM clients WHERE clients.client_name = %s AND clients.serverID = %s;"
        sql_data = (client_name, server_name,)

        try:
            self.cursor.execute(sql_query, sql_data)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not delete client-server peering of {client_name}-{server_name}.: %s", error)
            return 500
        else:
            logging.debug(f"Succesfully deleted client-server peer {client_name}-{server_name}.")
            return 200

    def assign_lease(self, client_name, server_name):
        """
        This method will assign a wireguard IP address to a client that will be used to communicate to the server within the wireguard session.
        This method should not be called directly as it is called from within the create_client() method.
        """
        ip_address = self.get_next_ip(server_name)
        if ip_address == None:
            return False
        clientID = self.get_client_id(client_name, server_name)

        sql_query = "INSERT INTO leases (subnetID, clientID, ip_address) VALUES ((SELECT subnetID FROM subnets WHERE serverID = %s), %s, %s );"
        sql_data =  (server_name, clientID, ip_address,)

        try:
            self.cursor.execute(sql_query, sql_data)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            logging.error(f"Could not assign lease to client {client_name}: %s", error)
            return False
        else:
            logging.debug(f"Successfully added client: {client_name}.")
            return True

    def get_next_ip(self, server_name):
        """
        This method returns the next unassigned IP address from the subnet owned by a server.
        """

        sql_reserved_ips_query = "SELECT leases.ip_address FROM subnets INNER JOIN leases ON subnets.subnetID = leases.subnetID WHERE subnets.serverID = %s;"
        sql_reserved_ips_data = (server_name,)
        sql_subnet_details_query = "SELECT network_address, network_mask, n_reserved_ips FROM subnets WHERE serverID = %s;"
        sql_subnet_details_data = (server_name,)

        try:
            self.cursor.execute(sql_reserved_ips_query, sql_reserved_ips_data)
            taken_ips = self.cursor.fetchall()
            self.cursor.execute(sql_subnet_details_query, sql_subnet_details_data)
            network_address, network_mask, n_reserved_ips = self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Failed to retrieve details of subnet for client {server_name}: %s", error)
        subnet = ipaddress.ip_network(f"{network_address}/{network_mask}")
        
        #Set it to the first available ip if none exist.
        if len(taken_ips) == 0:
            if subnet[n_reserved_ips + 1] != subnet[-1]:
                return str(subnet[n_reserved_ips + 1])
            else:
                return None

        #Return first IP address not in use
        for ipaddr in subnet.hosts():
            ipaddr_str = (str(ipaddr),)
            ipaddr = ipaddress.ip_address(ipaddr)
            if not ipaddr_str in taken_ips and ipaddr > subnet[n_reserved_ips] and ipaddr != subnet[-1]:
                return ipaddr_str
        
        return None

    def list_clients(self):
        """
        Returns all columns of all rows within the clients table.
        """
        response = {}
        sql_query = "SELECT * FROM clients;"

        try:
            self.cursor.execute(sql_query)
            clients =  self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull client list from database: %s", error)
        for client in clients:
            if not(client[1] in response.keys()):
                response[client[1]] = {}
            response[client[1]][client[0]] = {"public_key": client[2], "server": client[3]}
        return response


    def list_servers(self):
        """
        Returns all columns of all rows within the servers table.
        """
        response = {}
        sql_query = "SELECT * FROM servers;"
        try:
            self.cursor.execute(sql_query)
            servers = self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull server list from database: %s", error)
        for server in servers:
            response[server[0]] = {"public_key": server[1], "endpoint_address": server[2], "endpoint_port": server[3]}
        return response

    def list_leases(self):
        """
        Returns all columns of all rows within the leases table.
        """

        sql_query = "SELECT * FROM leases;"

        try:
            self.cursor.execute(sql_query)
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull client list from database: %s", error)

    def list_subnets(self):
        """
        Returns all columns of all rows within the subnets table.
        """

        sql_query = "SELECT * FROM subnets;"

        try:
            self.cursor.execute(sql_query)
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull client list from database: %s", error)

    def get_client_id(self, client_name, server_name):
        """
        Returns the Primary Key ID of the peering between the specified client and server.
        """

        sql_query = "SELECT clientID FROM clients WHERE client_name = %s AND serverID = %s;"
        sql_data = (client_name, server_name,)

        try:
            self.cursor.execute(sql_query, sql_data)
            return self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull client list from database: %s", error)
    
    def get_subnet_id(self, server_name):
        """
        Returns the Primary Key ID of the subnet assigned to the specified server.
        """

        sql_query = "SELECT subnetID FROM subnets WHERE serverID = %s;"
        sql_data = (server_name,)

        try:
            self.cursor.execute(sql_query, sql_data)
            return self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull client list from database: %s", error)

    def get_client_config(self, client_name, server_name):
        """
        Returns all non-sensitive details required for a client to configure itself for the peering with a single server.
        """
        if not self.check_client_exists(client_name, server_name):
            return None
        clientID = self.get_client_id(client_name, server_name)

        sql_server_query = "SELECT public_key, endpoint_address, endpoint_port FROM servers WHERE serverID = %s;"
        sql_server_data = (server_name,)
        sql_subnet_query = "SELECT subnets.allowed_ips, leases.ip_address FROM subnets INNER JOIN leases ON leases.subnetID = subnets.subnetID WHERE leases.clientID = %s;"
        sql_subnet_data = (clientID,)

        try:
            self.cursor.execute(sql_server_query, sql_server_data)
            server_details = self.cursor.fetchone()

            self.cursor.execute(sql_subnet_query, sql_subnet_data)
            subnet_details = self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull client details from database: %s", error)
        server_details = {"public_key": server_details[0], "endpoint_address": server_details[1], "endpoint_port": server_details[2]}
        subnet_details = {"allowed_ips": subnet_details[0], "lease": subnet_details[1]}
        response = {"server": server_details, "subnet": subnet_details}
        return response

    def get_server_config(self, server_name):
        """
        Returns all client details required for a server to configure itself to accept connections from those clients.
        """
        if not self.check_server_exists(server_name):
            return None
        subnetID = self.get_subnet_id(server_name)
        response = {"peers": []}

        sql_query = "SELECT clients.clientID, clients.public_key, leases.ip_address FROM clients INNER JOIN leases ON clients.clientID = leases.clientID WHERE subnetID = %s;"
        sql_data = (subnetID,)

        try:
            self.cursor.execute(sql_query, sql_data)
            clients = self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull client list from database: %s", error)
            return {}
        for client in clients:
            response["peers"] += [{"public_key": client[1], "ip_address": client[2]}]
        return response

    def check_server_exists(self, server_name):
        """ Checks if a server exists """
        sql_query = "SELECT COUNT(serverID) FROM servers WHERE serverID = %s;"
        sql_data = (server_name,)
        try:
            self.cursor.execute(sql_query, sql_data)
            instances_of_server = self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not reach database: %s", error)
        return instances_of_server > 0

    def check_client_exists(self, client_name, server_name):
        """ Checks if a server exists """
        sql_query = "SELECT COUNT(clientID) FROM clients WHERE client_name = %s AND serverID = %s;"
        sql_data = (client_name, server_name)
        try:
            self.cursor.execute(sql_query, sql_data)
            instances_of_client = self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not reach database: %s", error)
        return instances_of_client > 0

    def validate_wg_key(self, key):
        """
        Returns whether a given string represents a valid wireguard key.
        """
        pattern = re.compile("^[0-9a-zA-Z\+/]{43}=")
        return pattern.match(key) != None
    
    def validate_ip(self, ip):
        """ Checks if ip is a valid IPv4 Address. """
        try:
            ipaddress.IPv4Address(ip)
            return True
        except (Exception, ValueError):
            return False

    def validate_network_mask(self, mask):
        """ Checks if network mask is a valid IPv4 mask. """
        try:
            return mask > 0 and mask <=32
        except Exception:
            return False

    def validate_port(self, port):
        """ Checks if port number is within the valid range. """
        try:
            return port > 1 and port <=65535
        except Exception:
            return False

    def get_server_wireguard_ip(self, server_name):
        """ Returns the IP address assigned to a server for use within its wireguard session. """
        subnetID = self.get_subnet_id(server_name)
        response = {}

        sql_query = "SELECT server_ip FROM subnets WHERE subnetID = %s"
        sql_data = (subnetID,)

        try:
            self.cursor.execute(sql_query, sql_data)
            response["server_wg_ip"] = self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(f"Could not pull servers wireguard ip from database: %s", error)
        return response
