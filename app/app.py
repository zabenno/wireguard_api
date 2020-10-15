from flask import Flask, jsonify, render_template, request
from wireguard_db import Wireguard_database
from waitress import serve
from functools import wraps
from time import sleep
import os, logging

#Import Database and API server creds from environment variables.
server = os.environ.get('DB_SERVER')
port = os.environ.get('DB_PORT')
database = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
with open(os.environ.get('DB_PASSWORD_PATH'),'r') as db_password_file:
    db_password = db_password_file.read()
api_username = os.environ.get('API_USER')
with open(os.environ.get('API_PASSWORD_PATH'),'r') as api_password_file:
    api_password = api_password_file.read()

wireguard_state = None

while wireguard_state == None:
    try:
        wireguard_state = Wireguard_database(db_server=server, db_port=port, db_database=database, db_user=db_user,db_password=db_password)
    except (Exception) as error:
        logging.error("An error occured while connecting to the database.")
    if wireguard_state == None:
        sleep(5)

app = Flask(__name__)

#VERY basic implementation of http-basic authentication.
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == api_username and auth.password == api_password:
            return f(*args, **kwargs)
        return "", 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'}
    return decorated


@app.route('/api/v1/client/list_all', methods=["GET"])
@auth_required
def return_client_list():
    return jsonify(wireguard_state.list_clients())

@app.route('/api/v1/server/list_all', methods=["GET"])
@auth_required
def return_servers_list():
    return jsonify(wireguard_state.list_servers())

#Return all non-sensitive information required to configure a specified wireguard server.
@app.route('/api/v1/server/config/', methods=["GET"])
@auth_required
def return_server_conf():
    content = request.json
    response = wireguard_state.get_server_config(content['server_name'])
    if response == None:
        return "", 404
    elif response == {}:
        return "", 500
    else:
        return response, 200

#Return all non-sensitive information required to configure a specific client-server peering.
@app.route('/api/v1/client/config/', methods=["GET"])
def get_client_conf():
    content = request.json
    try:
        response = wireguard_state.get_client_config(content['client_name'], content['server_name'])
    except Exception:
        return "", 500
    if response == None:
        return "", 404
    else:
        return response, 200

#Create a new wireguard server.
@app.route('/api/v1/server/add/', methods=['POST'])
@auth_required
def create_server():
    content = request.json
    response_code = wireguard_state.create_server(content['server_name'], content['network_address'], content['network_mask'], content['public_key'], content['endpoint_address'], content['endpoint_port'], content['n_reserved_ips'], content['allowed_ips'])
    return "", response_code

#Create a new wireguard server.
@app.route('/api/v1/server/wireguard_ip/', methods=['GET'])
@auth_required
def get_server_wireguard_ip():
    content = request.json
    response = wireguard_state.get_server_wireguard_ip(content['server_name'])
    if len(response) > 0:
        return response, 200
    else:
        return "", 404

#Check if a wireguard server exists.
@app.route('/api/v1/server/exists/', methods=['GET'])
@auth_required
def get_server_existance():
    content = request.json
    exists = wireguard_state.check_server_exists(content['server_name'])
    if exists:
        return "", 200
    else:
        return "", 404

#Create a new client-server peering.
@app.route('/api/v1/client/add/', methods=['POST'])
@auth_required
def create_client():
    content = request.json
    response_code = wireguard_state.create_client(content['client_name'], content['server_name'], content['public_key'])
    return "", response_code


#Remove all instances of a client with a specified host name.
@app.route('/api/v1/client/delete/', methods=['POST'])
@auth_required
def delete_client():
    content = request.json
    return "", wireguard_state.delete_client(content['client_name'])

#Removes a server and any row in the database referencing it.
@app.route('/api/v1/server/delete/', methods=['POST'])
@auth_required
def delete_server():
    content = request.json
    return "", wireguard_state.delete_server(content['server_name'])

#Removes the peering instance of a specified client from a specified server.
@app.route('/api/v1/server/remove_peer/', methods=['POST'])
@auth_required
def remove_peer():
    content = request.json
    return "", wireguard_state.delete_client_peering(content['client_name'], content['server_name'])

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
#    app.run(debug=1)
