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

def get_shoppingList(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM shopping_list;")
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            inventory = [dict(zip(colnames, row)) for row in rows]
            return jsonify(inventory)
    except Exception as error:
        return jsonify({'error': str(error)}), 500

def add_shoppingList_item(conn, new_item):
    try:
        articolo = new_item.get('articolo')
        quantità = new_item.get('quantità')

        if not articolo or not isinstance(articolo, str):
            return jsonify({'error': 'Il campo "articolo" deve essere una stringa e non può essere vuoto.'}), 400

        if quantità is None or not isinstance(quantità, (int, float)):
            return jsonify({'error': 'Il campo "quantità" deve essere un numero.'}), 400

        with conn.cursor() as cursor:
            # Controlla se l'articolo esiste già nella shopping_list
            cursor.execute("SELECT quantità FROM shopping_list WHERE articolo = %s;", (articolo,))
            result = cursor.fetchone()

            if result:
                # Se l'articolo esiste, somma la nuova quantità alla quantità esistente
                nuova_quantità = result[0] + quantità
                cursor.execute(
                    "UPDATE shopping_list SET quantità = %s WHERE articolo = %s;",
                    (nuova_quantità, articolo)
                )
                conn.commit()
                return jsonify({'message': 'Quantità aggiornata con successo'}), 200
            else:
                # Se l'articolo non esiste, aggiungi un nuovo articolo
                cursor.execute(
                    "INSERT INTO shopping_list (articolo, quantità) VALUES (%s, %s);",
                    (articolo, quantità)
                )
                conn.commit()
                return jsonify({'message': 'Articolo aggiunto con successo'}), 201

    except Exception as error:
        return jsonify({'error': str(error)}), 500


def delete_shoppingList_item(conn, articolo):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM shopping_list WHERE articolo = %s;", (articolo,)
            )
            conn.commit()
            return jsonify({'message': f'Articolo {articolo} eliminato con successo'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 500