from wireguard_db import Wireguard_database
import unittest

class unittest_wireguard_server(unittest.TestCase):      
    
    def test_create_server_expected(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(201, result)
        
    def test_create_server_bad_net_addr(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.create_server("wireguard01", "192.168.2", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(400, result)

    def test_create_server_bad_net_mask(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.create_server("wireguard01", "192.168.2.0", 33, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(400, result)
    
    def test_create_server_bad_key(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.create_server("wireguard01", "192.168.2.0", 33, "sdfser", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(400, result)
    
    def test_create_server_bad_port(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.create_server("wireguard01", "192.168.2.0", 33, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 512800, 20, "192.168.2.0/32")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(400, result)
    
    def test_delete_server_expected(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 33, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.delete_server("wireguard01")
        self.assertEqual(200, result)

    def test_delete_server_nonexistent(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.delete_server("wireguard01")
        self.assertEqual(200, result)
    
    def test_delete_server_bad_connection(self):
        wireguard_state = Wireguard_database()
        wireguard_state.cursor = None
        result = wireguard_state.delete_server("wireguard01")
        self.assertEqual(500, result)
    
    def test_server_config_expected(self):
        expected_result = { 
            "peers": [
                { 
                    "ip_address": "192.168.2.21",
                    "public_key": "gjXsuVSwfiqiZkf/rcEV8KszlTF4BseS4zY6dnKjCXc="
                }
            ]
        }

        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        wireguard_state.create_client("testclient1", "wireguard01", "gjXsuVSwfiqiZkf/rcEV8KszlTF4BseS4zY6dnKjCXc=")
        result = wireguard_state.get_server_config("wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(expected_result, result)

    def test_server_config_no_peers(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.get_server_config("wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual({"peers": []}, result)

    def test_server_config_nonexistent(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.get_server_config("wireguard01")
        self.assertEqual(None, result)

    def test_server_exists_absent(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.check_server_exists("wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(False, result)

    def test_server_exists_present(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.check_server_exists("wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(True, result)
    
if __name__ == '__main__':
    unittest.main()