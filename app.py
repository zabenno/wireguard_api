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

@app.route('/api/v1/server/config/', methods=["GET"])
def return_server_conf():
    content = request.json
    try:
        response = test.get_server_config(content['server_name']), 200
    except (Exception):
        return f"Failed to retrieve {content['server_name']} configuration.", 500
    print(response)
    if len(response[0]) == 0:
        return "Server not found.", 404
    return response

@app.route('/api/v1/client/config/', methods=["GET"])
def get_client_conf():
    content = request.json
    try:
        return test.get_client_config(content['client_name'], content['server_name']), 200
    except (Exception):
        return "Could not retrieve client configuration", 500

@app.route('/api/v1/server/add/', methods=['POST'])
def create_server():
    content = request.json
    try:
        test.create_server(content['server_name'], content['network_address'], content['network_mask'], content['public_key'], content['endpoint_address'], content['endpoint_port'], content['n_reserved_ips'])
        return f"Created {content['server_name']} server.", 201
    except (Exception):
        return f"Failed to create {content['server_name']} server.", 500

@app.route('/api/v1/client/add/', methods=['POST'])
def create_client():
    content = request.json
    try:
        test.create_client(content['client_name'], content['server_name'], content['public_key'])
        return f"Created {content['client_name']} client.", 201
    except (Exception):
        return f"Failed to create {content['client_name']} client.", 500

@app.route('/api/v1/client/delete/', methods=['POST'])
def delete_client():
    content = request.json
    try:
        test.delete_client(content['client_name'])
        return f"Deleted {content['client_name']} client.", 200
    except (Exception):
        return f"Failed to create {content['client_name']} client.", 500

@app.route('/api/v1/server/delete/', methods=['POST'])
def delete_server():
    content = request.json
    try:
        test.delete_server(content['server_name'])
        return f"Deleted {content['server_name']} server.", 200
    except (Exception):
        return f"Failed to create {content['server_name']} server.", 500

@app.route('/api/v1/server/remove_peer/', methods=['POST'])
def remove_peer():
    content = request.json
    try:
        test.delete_client_peering(content['client_name'], content['server_name'])
        return f"Removed peer {content['client_name']} from {content['server_name']} server.", 200
    except (Exception):
        return f"Failed to remove peer {content['client_name']} from {content['server_name']} server.", 500

if __name__ == "__main__":
    app.run(debug=1)