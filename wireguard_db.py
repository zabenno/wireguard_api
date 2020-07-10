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
            print(type(self.cursor))
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

    def create_server(self, server_name, network_address, network_mask, public_key, endpoint_address, endpoint_port, n_reserved_ips):
        try:
            self.cursor.execute("""
            INSERT INTO servers (serverID, public_key, endpoint_address, endpoint_port) VALUES ( %s, %s, %s, %s)
            """, (server_name, public_key, endpoint_address, endpoint_port))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not add server {server_name}: ", error)
        else:
            print(f"Debug: Successfully added server: {server_name}.")
        self.create_subnet(server_name, network_address, network_mask, n_reserved_ips)

    def delete_server(self, server_name):
        try:
            self.cursor.execute("DELETE FROM servers WHERE servers.serverID = %s;", (server_name,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not delete server {server_name}.: ", error)
        else:
            print(f"Debug: Succesfully deleted server {server_name}.")
    
    def create_subnet(self, server_name, network_address, network_mask, n_reserved_ips):
        try:
            self.cursor.execute("""
            INSERT INTO subnets (serverID, network_address, network_mask, n_reserved_ips ) VALUES ( %s, %s, %s, %s )
            ;""", (server_name, network_address, network_mask, n_reserved_ips,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not add subnet for {server_name}: ", error)
        else:
            print(f"Debug: Successfully added subnet: {network_address}/{network_mask}.")

    def create_client(self, client_name, server_name, public_key):
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
        try:
            self.cursor.execute("""
            INSERT INTO leases (subnetID, clientID, ip_address) VALUES (
            (SELECT subnetID FROM subnets WHERE serverID = %s),
            (SELECT clientID FROM clients WHERE client_name = %s),
            %s );""", (server_name, client_name, ip_address,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not assign lease to client {client_name}: ", error)
        else:
            print(f"Debug: Successfully added client: {client_name}.")

    def get_next_ip(self, server_name):
        next_ip = ""
        try:
            self.cursor.execute("""SELECT leases.ip_address FROM subnets INNER JOIN leases ON subnets.subnetID = leases.subnetID 
            WHERE subnets.serverID = %s;""", (server_name,))
            taken_ips = self.cursor.fetchall()
            self.cursor.execute("SELECT network_address, network_mask, n_reserved_ips FROM subnets WHERE serverID = %s", (server_name,))
            network_address, network_mask, n_reserved_ips = self.cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve details of subnet for client {server_name}: ", error)
        subnet = ipaddress.ip_network(f"{network_address}/{network_mask}")
        for ipaddr in subnet.hosts():
            if not(ipaddr in taken_ips) and ipaddr > subnet[n_reserved_ips]:
                next_ip = ipaddr
                break
        print(str(next_ip))
        if len(str(next_ip)) == 0:
            raise Exception("Error: Server out of leases")
        ipaddr = ipaddress.ip_address(next_ip)
        intaddr = int.from_bytes(ipaddr.packed, "big")
        return intaddr

    def list_clients(self):
        try:
            self.cursor.execute("SELECT * FROM clients;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: Could not pull client list from database: ", error)

test = Wireguard_database()
print(test.list_clients())
#test.delete_client("testclient1")
test.create_server("wireguard01", "192.168.2.0", 24, "SSHHUUBBWW", "192.168.2.55", 5128, 20)
#test.create_server("wireguard02", "192.168.1.0", 24, "SSHHUUBfBWW", "192.168.2.55", 5128, 20)
test.create_client("testclient1", "wireguard01", "JJIINNPPSS")
test.delete_client("testclient1")
test.assign_lease("testclient1", "wireguard01")