from flask import Flask, jsonify, render_template, request
from wireguard_db import Wireguard_database

test = Wireguard_database()

app = Flask(__name__)

@app.route('/api/v1/clients/list_all', methods=["GET"])
def return_client_list():
    return jsonify(test.list_clients())

@app.route('/api/v1/leases/list_all', methods=["GET"])
def return_leases_list():
    return jsonify(test.list_leases())

@app.route('/api/v1/servers/list_all', methods=["GET"])
def return_servers_list():
    return jsonify(test.list_servers())

@app.route('/api/v1/server/<server_name>', methods=["GET"])
def return_server_conf(server_name):
    try:
        response = test.get_server_config(server_name), 200
    except (Exception) as error:
        return f"Failed to retrieve {server_name} configuration.", 500
    print(response)
    if len(response[0]) == 0:
        return "Server not found.", 404
    return response

@app.route('/api/v1/config/<server_name>/<client_name>', methods=["GET"])
def get_client_conf(client_name, server_name):
    print(client_name)
    response = test.get_client_config(client_name, server_name)
    print(response)
    return response

@app.route('/api/v1/server/add/', methods=['POST'])
def create_server():
    content = request.json
    try:
        test.create_server(content['server_name'], content['network_address'], content['network_mask'], content['public_key'], content['endpoint_address'], content['endpoint_port'], content['n_reserved_ips'])
        return f"Created {content['server_name']} server.", 201
    except (Exception) as error:
        return f"Failed to create {content['server_name']} server.", 500

if __name__ == "__main__":
    app.run(debug=1)