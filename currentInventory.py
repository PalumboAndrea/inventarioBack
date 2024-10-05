import psycopg2
from flask import jsonify
from config import load_config

def connect(config):
    """ Connect to the PostgreSQL database server """
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            print('Connected to the PostgreSQL server.')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
        return None

def get_inventory(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM current_inventory;")
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            inventory = [dict(zip(colnames, row)) for row in rows]
            return jsonify(inventory)
    except Exception as error:
        return jsonify({'error': str(error)}), 500

def add_inventory_item(conn, new_item):
    try:
        articolo = new_item.get('articolo')
        quantità = new_item.get('quantità')

        if not articolo or not isinstance(articolo, str):
            return jsonify({'error': 'Il campo "articolo" deve essere una stringa e non può essere vuoto.'}), 400

        if quantità is None or not isinstance(quantità, (int, float)):
            return jsonify({'error': 'Il campo "quantità" deve essere un numero.'}), 400

        with conn.cursor() as cursor:
            # Verifica se l'articolo esiste già
            cursor.execute("SELECT quantità FROM current_inventory WHERE articolo = %s;", (articolo,))
            existing_item = cursor.fetchone()

            if existing_item:
                # Se l'articolo esiste, somma la quantità
                nuova_quantità = existing_item[0] + quantità
                cursor.execute(
                    "UPDATE current_inventory SET quantità = %s WHERE articolo = %s;",
                    (nuova_quantità, articolo)
                )
                message = f'Quantità di {articolo} aggiornata a {nuova_quantità}.'
            else:
                # Se l'articolo non esiste, inseriscilo
                cursor.execute(
                    "INSERT INTO current_inventory (articolo, quantità) VALUES (%s, %s);",
                    (articolo, quantità)
                )
                message = f'Articolo {articolo} aggiunto con successo.'

            conn.commit()
            return jsonify({'message': message}), 201
    except Exception as error:
        return jsonify({'error': str(error)}), 500

def update_inventory_item(conn, updated_item):
    """ Aggiorna un articolo esistente nell'inventario. """
    try:
        articolo = updated_item.get('articolo')
        quantità = updated_item.get('quantità')

        if not articolo or not isinstance(articolo, str):
            return jsonify({'error': 'Il campo "articolo" deve essere una stringa e non può essere vuoto.'}), 400

        if quantità is None or not isinstance(quantità, (int, float)):
            return jsonify({'error': 'Il campo "quantità" deve essere un numero.'}), 400

        with conn.cursor() as cursor:
            cursor.execute("UPDATE current_inventory SET quantità = %s WHERE articolo = %s;", (quantità, articolo))
            if cursor.rowcount == 0:
                return jsonify({'error': 'Articolo non trovato per l\'aggiornamento.'}), 404

            conn.commit()
            return jsonify({'message': f'Articolo {articolo} aggiornato con successo.'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 500

def delete_inventory_item(conn, articolo):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM current_inventory WHERE articolo = %s;", (articolo,)
            )
            conn.commit()
            return jsonify({'message': f'Articolo {articolo} eliminato con successo'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 500