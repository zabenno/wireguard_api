import ipaddress, psycopg2

class wireguard_ipam():
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
    create_subnet(cidr_range, n_reserved_ips)
        Creates a subnet with a restriction against using the first n ips.
    delete_subnet(cidr_range)
        Deletes a subnet.
    assign_subnet(cidr_range, serverID)
        Assigns a subnet to a defined server.
    create_lease(wg_client, wg_server)
        Creates an ip lease within a subnet.
    delete_lease(wg_client, wg_server)
        Removes an ip lease within a subnet.
    get_next_ip(cidr_range)
        Returns the next available ip in a subnet.
    get_servers_cidr(serverID)
        Returns the subnet of a server.
    get_client_ID(client_name, server_name)
        Returns the ID of a client-server pair.
    list_assigned_ips(cidr_range)
        Returns a list of all taken ips in a subnet.
    list_all_subnets()
        Returns a list of all subnets.
    """
    def __init__(self, db_connection, cursor):
        """
        Parameters
        ----------
        db_connection : psycopg2.extensions.connection
            The connection to the postgres database.
        db_cursor : psycopg2.extensions.cursor
            psycopg2 used for issuing commands to the database.
        """
        self.db_connection = db_connection
        self.cursor = cursor
    
    def create_subnet(self, cidr_range, n_reserved_ips):
        """
        Creates a subnet to be later assigned to a server.

        Parameters
        ----------
        cidr_range : str
            The cidr mask for the subnet e.g. 192.168.1.0/24
        n_reserved_ips : int
            The number of ips to reserve from the first portion of the subnet.
        """
        try:
            self.cursor.execute("""
            INSERT INTO subnets (cidr_range, n_reserved_ips ) VALUES ( %s, %s )
            ;""", (cidr_range, n_reserved_ips,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not add subnet: ", error)
        else:
            print(f"Debug: Successfully added subnet: {cidr_range}.")

    def delete_subnet(self, cidr_range):
        """
        Deletes a subnet.

        Parameters
        ----------
        cidr_range : str
            The subnet to be deleted e.g. 192.168.1.0/24
        """
        try:
            self.cursor.execute("""
            DELETE FROM subnets WHERE subnets.cidr_range =  %s;""", (cidr_range,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not delete subnet: ", error)
        else:
            print(f"Debug: Successfully deleted subnet: {cidr_range}.")

    def assign_subnet(self, cidr_range, serverID):
        """
        Assigns a defined subnet to a defined server.

        Parameters
        ----------
        cidr_range : str
            The subnet to be assigned to the server e.g. 192.168.1.0/24
        serverID : str
            The name of the server to assign the subnet to.
        """
        try:
            self.cursor.execute("""
            UPDATE subnets SET serverID = %s WHERE subnets.cidr_range = %s
            ;""", (serverID, cidr_range,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print("Error: Could not assign subnet to server ", error)
        else:
            print(f"Debug: Successfully assigned subnet {cidr_range} to {serverID}.")

    def create_lease(self, wg_client, wg_server):
        """
        Create a lease for a client to communicate to a server.

        Parameters
        ----------
        wg_client : str
            The name of the client receiving a lease.
        wg_server : str
            The name of the server the client will be served by.
        """
        clientID = self.get_client_ID(wg_client, wg_server)
        wg_servers_cidr = self.get_servers_cidr(wg_server)
        next_lease_available = self.get_next_ip(wg_servers_cidr)
        ipaddr = ipaddress.ip_address(next_lease_available)
        intaddr = int.from_bytes(ipaddr.packed, "big")

        try:
            self.cursor.execute("INSERT INTO leases (cidr_range, clientID, ip_address) VALUES ( %s, %s, %s);", (wg_servers_cidr, clientID, intaddr,))
            self.db_connection.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            self.db_connection.rollback()
            print(f"Error: Could not assign ip address {next_lease_available} to client {wg_client}: ", error)
        else:
            print(f"Debug: Successfully assigned ip address {ipaddr} to client {wg_client}")

    def delete_lease(self, wg_client, wg_server):
        """
        Delete a client lease from a servers subnet.

        Parameters
        ----------
        wg_client : str
            The name of the client losing the lease.
        wg_server : str
            The name of the server the client was assigned to.
        """
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
        """
        The next IP available within a subnet. (Assumes subnet will never fill up)

        Parameters
        ----------
        cidr_range : str
            The subnet to find the next ip in.
        """
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
        """
        Returns the subnet assigned to a server.

        Parameters
        ----------
        serverID : str
            The name of the server.
        """
        try:
            self.cursor.execute("SELECT cidr_range FROM subnets WHERE subnets.serverID = %s;", (serverID,))
            return self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve subnet for {serverID}: ", error)

    def get_client_ID(self, client_name, server_name):
        """
        Returns the ID of a client-server peer.

        Parameters
        ----------
        client_name : str
            The name of the client.
        server_name : str
            The name of the server.

        Returns
        -------
        int
            The ID of the client-server peer.
        """
        try:
            self.cursor.execute("SELECT clientID FROM clients WHERE clients.serverID = %s AND clients.client_name = %s;", (server_name,client_name))
            return self.cursor.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve ID for client {client_name}: ", error)

    def list_assigned_ips(self, cidr_range):
        """
        Lists all taken ips within a subnet.

        Parameters
        ----------
        cidr_range : str
            The subnet to check e.g. 192.168.1.0/24

        Returns
        -------
        list
            A list of all take ips.
        """
        try:
            self.cursor.execute("SELECT ip_address FROM leases WHERE leases.cidr_range = %s;", (cidr_range,))
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve leases for subnet {cidr_range}: ", error)

    def list_all_subnets(self):
        """
        Lists all subnets defined.

        Returns
        -------
        list
            A list of all subnets that are currently defined.
        """
        try:
            self.cursor.execute("SELECT * FROM subnets;")
            return self.cursor.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: Failed to retrieve subnets: ", error)