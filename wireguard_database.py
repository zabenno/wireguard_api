import psycopg2

class Wireguard_database():
    def __init__(self, db_server="127.0.0.1", db_port="5432", db_database="postgres", db_user="postgres", db_password="changeme123"):
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
                ip_address VARCHAR (15) UNIQUE,
                public_key VARCHAR (40) UNIQUE,
                serverID VARCHAR (20),
                CONSTRAINT clients_serverID_fkey FOREIGN KEY (serverID) 
                REFERENCES wg_servers (serverID) MATCH SIMPLE
            );
            """)
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not create database, failed with error: ", error)
        else:
            print("Debug: Successfully formatted database.")