from flask import Flask, jsonify, render_template, request
from wireguard_db import Wireguard_database
from waitress import serve
from functools import wraps
import os

server = os.environ.get('DB_SERVER')
port = os.environ.get('DB_PORT')
database = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
with open(os.environ.get('DB_PASSWORD_PATH'),'r') as f:
    db_password = f.read()
api_username = os.environ.get('API_USER')
with open(os.environ.get('API_PASSWORD_PATH'),'r') as f:
    api_password = f.read()

test = Wireguard_database(db_server=server, db_port=port, db_database=database, db_user=db_user,db_password=db_password)

app = Flask(__name__)

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == api_username and auth.password == api_password:
            return f(*args, **kwargs)
        return "Invalid login.", 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'}
    return decorated

@app.route('/api/v1/client/list_all', methods=["GET"])
@auth_required
def return_client_list():
    return jsonify(test.list_clients())

@app.route('/api/v1/server/list_all', methods=["GET"])
@auth_required
def return_servers_list():
    return jsonify(test.list_servers())

@app.route('/api/v1/server/config/', methods=["GET"])
@auth_required
def return_server_conf():
    content = request.json
    try:
        response = test.get_server_config(content['server_name']), 200
    except (Exception):
        return f"Failed to retrieve {content['server_name']} configuration.", 500
    if len(response[0]) == 0:
        return "Server not found.", 404
    return response

@app.route('/api/v1/client/config/', methods=["GET"])
@auth_required
def get_client_conf():
    content = request.json
    try:
        return test.get_client_config(content['client_name'], content['server_name']), 200
    except (Exception):
        return "Could not retrieve client configuration", 500

@app.route('/api/v1/server/add/', methods=['POST'])
@auth_required
def create_server():
    content = request.json
    try:
        test.create_server(content['server_name'], content['network_address'], content['network_mask'], content['public_key'], content['endpoint_address'], content['endpoint_port'], content['n_reserved_ips'], content['allowed_ips'])
        return f"Created {content['server_name']} server.", 201
    except (Exception):
        return f"Failed to create {content['server_name']} server.", 500

@app.route('/api/v1/client/add/', methods=['POST'])
@auth_required
def create_client():
    content = request.json
    try:
        test.create_client(content['client_name'], content['server_name'], content['public_key'])
        return f"Created {content['client_name']} client.", 201
    except (Exception):
        return f"Failed to create {content['client_name']} client.", 500

@app.route('/api/v1/client/delete/', methods=['POST'])
@auth_required
def delete_client():
    content = request.json
    try:
        test.delete_client(content['client_name'])
        return f"Deleted {content['client_name']} client.", 200
    except (Exception):
        return f"Failed to create {content['client_name']} client.", 500

@app.route('/api/v1/server/delete/', methods=['POST'])
@auth_required
def delete_server():
    content = request.json
    try:
        test.delete_server(content['server_name'])
        return f"Deleted {content['server_name']} server.", 200
    except (Exception):
        return f"Failed to create {content['server_name']} server.", 500

@app.route('/api/v1/server/remove_peer/', methods=['POST'])
@auth_required
def remove_peer():
    content = request.json
    try:
        test.delete_client_peering(content['client_name'], content['server_name'])
        return f"Removed peer {content['client_name']} from {content['server_name']} server.", 200
    except (Exception):
        return f"Failed to remove peer {content['client_name']} from {content['server_name']} server.", 500

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
#    app.run(debug=1)
