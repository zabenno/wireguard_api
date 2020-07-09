import psycopg2

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
            CREATE TABLE wg_servers (
                serverID VARCHAR (20) PRIMARY KEY,
                public_key VARCHAR (40) UNIQUE,
                ip_address VARCHAR (15) UNIQUE,
                wg_ip_range VARCHAR (18) UNIQUE,
                wg_ip_address VARCHAR (15) UNIQUE
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
                REFERENCES wg_servers (serverID) MATCH SIMPLE
            );
            """)
            self.db_connection.commit()
            self.cursor.execute("""
            CREATE TABLE subnets (
                subnetID serial PRIMARY KEY,
                cidr_range VARCHAR (18) UNIQUE,
                n_reserved_ips INT,
                serverID VARCHAR (20),
                CONSTRAINT subnets_serverID_fkey FOREIGN KEY (serverID) 
                REFERENCES wg_servers (serverID) MATCH SIMPLE
            );
            """)
            self.db_connection.commit()
            self.cursor.execute("""
            CREATE TABLE leases (
                leaseID serial PRIMARY KEY,
                cidr_range VARCHAR (18),
                clientID serial UNIQUE,
                ip_address INT,
                CONSTRAINT leases_clientID_fkey FOREIGN KEY (clientID) 
                REFERENCES clients (clientID) MATCH SIMPLE,
                CONSTRAINT leases_cidr_range_fkey FOREIGN KEY (cidr_range) 
                REFERENCES subnets (cidr_range) MATCH SIMPLE
            );
            """)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not create database, failed with error: ", error)
        else:
            print("Debug: Successfully formatted database.")