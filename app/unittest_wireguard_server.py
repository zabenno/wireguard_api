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
    
    def test_server_wg_ip_present(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.get_server_wireguard_ip("wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual({'server_wg_ip': '192.168.2.1'}, result)
    
    def test_server_wg_ip_absent(self):
        wireguard_state = Wireguard_database()
        result = wireguard_state.get_server_wireguard_ip("wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual({}, result)
    
    def test_client_create_expected(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.create_client("testclient01", "wireguard01", "XxXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(201, result)
    
    def test_client_create_bad_key(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.create_client("testclient01", "wireguard01", "xXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(400, result)
    
    def test_client_create_bad_server(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.create_client("testclient01", "wireguard02", "XxXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(404, result)
    
    def test_client_create_no_lease(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 254, "192.168.2.0/32")
        result = wireguard_state.create_client("testclient01", "wireguard01", "XxXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(500, result)

    def test_client_config_expected(self):
        expected = {
            'server': 
            {
                    'public_key': 'gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=', 
                    'endpoint_address': '192.168.2.55', 
                    'endpoint_port': 5128
                    },
            'subnet': 
                {
                'allowed_ips': '192.168.2.0/32',
                 'lease': '192.168.2.21'
                 }
            }
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        wireguard_state.create_client("testclient01", "wireguard01", "XxXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=")
        result = wireguard_state.get_client_config("testclient01", "wireguard01")
        print(wireguard_state.get_client_config("testclient01", "wireguard01"))
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(expected, result)

    def test_client_config_absent(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.get_client_config("testclient01", "wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(None, result)

    def test_client_exists_absent(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        result = wireguard_state.check_client_exists("testclient01", "wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(False, result)

    def test_client_exists_present(self):
        wireguard_state = Wireguard_database()
        wireguard_state.create_server("wireguard01", "192.168.2.0", 24, "gjXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=", "192.168.2.55", 5128, 20, "192.168.2.0/32")
        wireguard_state.create_client("testclient01", "wireguard01", "XxXnuVSwfiqiZkf/rcEV8KczlTF4BseS4zY6dnKjCXc=")
        result = wireguard_state.check_client_exists("testclient01", "wireguard01")
        wireguard_state.delete_server("wireguard01")
        self.assertEqual(True, result)

if __name__ == '__main__':
    unittest.main()