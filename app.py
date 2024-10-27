from flask import Flask, jsonify, request
from flask_cors import CORS
from currentInventory import connect, get_inventory, add_inventory_item, delete_inventory_item, update_inventory_item
from shoppingList import connect as connect_shopping, get_shoppingList, add_shoppingList_item, delete_shoppingList_item
from mustBe import connect as connect_mustbe, get_mustBeItems, add_mustBe_item, delete_mustBe_item, update_mustBe_item
from config import load_config

app = Flask(__name__)
CORS(app)

@app.route('/api/inventory', methods=['GET'])
def api_get_inventory():
    config = load_config()
    conn = connect(config)
    if conn:
        response = get_inventory(conn)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/inventory', methods=['POST'])
def api_add_inventory_item():
    config = load_config()
    conn = connect(config)
    if conn:
        new_item = request.get_json()
        response = add_inventory_item(conn, new_item)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/inventory/<string:articolo>', methods=['PUT'])
def api_update_inventory_item(articolo):
    config = load_config()
    conn = connect(config)
    if conn:
        updated_item = request.get_json()
        response = update_inventory_item(conn, updated_item)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/inventory/<string:articolo>', methods=['DELETE'])
def api_delete_inventory_item(articolo):
    config = load_config()
    conn = connect(config)
    if conn:
        response = delete_inventory_item(conn, articolo)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/shoppingList', methods=['GET'])
def api_get_shoppingList():
    config = load_config()
    conn = connect(config)
    if conn:
        response = get_shoppingList(conn)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/shoppingList', methods=['POST'])
def api_add_shoppingList_item():
    config = load_config()
    conn = connect(config)
    if conn:
        new_item = request.get_json()
        response = add_shoppingList_item(conn, new_item)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/shoppingList/<string:articolo>', methods=['DELETE'])
def api_delete_shoppingList_item(articolo):
    config = load_config()
    conn = connect(config)
    if conn:
        response = delete_shoppingList_item(conn, articolo)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/mustbe', methods=['GET'])
def api_get_mustBeItems():
    config = load_config()
    conn = connect(config)
    if conn:
        response = get_mustBeItems(conn)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/mustbe', methods=['POST'])
def api_add_mustBe_item():
    config = load_config()
    conn = connect(config)
    if conn:
        new_item = request.get_json()
        response = add_mustBe_item(conn, new_item)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500

@app.route('/api/mustbe/<articolo>', methods=['PUT'])
def update_item(articolo):
    conn = connect(load_config())
    if conn:
        updated_item = request.json
        return update_mustBe_item(conn, articolo, updated_item)
    return jsonify({'error': 'Connessione al database fallita.'}), 500

@app.route('/api/mustbe/<string:articolo>', methods=['DELETE'])
def api_delete_mustBe_item(articolo):
    config = load_config()
    conn = connect(config)
    if conn:
        response = delete_mustBe_item(conn, articolo)
        conn.close()
        return response
    return jsonify({'error': 'Connection to database failed'}), 500


if __name__ == '__main__':
    app.run(debug=True)
