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

def get_mustBeItems(conn):
    try:
        with conn.cursor() as cursor:
            # LEFT JOIN tra mustbe e current_inventory per ottenere la quantità disponibile
            cursor.execute("""
                SELECT 
                    mustbe.articolo, 
                    mustbe.quantità,
                    COALESCE(current_inventory.quantità, 0) AS inventory_quantità,
                    (COALESCE(current_inventory.quantità, 0) >= mustbe.quantità) AS inCurrentInventory
                FROM mustbe
                LEFT JOIN current_inventory 
                ON mustbe.articolo = current_inventory.articolo;
            """)
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            inventory = [dict(zip(colnames, row)) for row in rows]
            
            # Cicla su ogni articolo per verificare se deve essere aggiunto alla shopping list
            for item in inventory:
                articolo = item['articolo']
                quantità = item['quantità']
                inventory_quantità = item['inventory_quantità']
                
                # Se la quantità nell'inventario è inferiore alla quantità richiesta in mustbe
                if inventory_quantità < quantità:
                    quantità_mancante = quantità - inventory_quantità
                    
                    # Controlla se l'articolo è già nella shopping_list
                    cursor.execute("SELECT quantità FROM shopping_list WHERE articolo = %s;", (articolo,))
                    result = cursor.fetchone()

                    if result:
                        # Se esiste già nella shopping_list
                        if result[0] < quantità_mancante:
                            # Se la quantità esistente è minore della quantità mancante, aggiorna la shopping list
                            nuova_quantità = result[0] + quantità_mancante
                            cursor.execute(
                                "UPDATE shopping_list SET quantità = %s WHERE articolo = %s;",
                                (nuova_quantità, articolo)
                            )
                    else:
                        # Se non esiste, inserisci il nuovo articolo nella shopping_list
                        cursor.execute(
                            "INSERT INTO shopping_list (articolo, quantità) VALUES (%s, %s);",
                            (articolo, quantità_mancante)
                        )
                    conn.commit()

            return jsonify(inventory)
    except Exception as error:
        return jsonify({'error': str(error)}), 500

def add_mustBe_item(conn, new_item):
    try:
        articolo = new_item.get('articolo')
        quantità = new_item.get('quantità')

        if not articolo or not isinstance(articolo, str):
            return jsonify({'error': 'Il campo "articolo" deve essere una stringa e non può essere vuoto.'}), 400

        if quantità is None or not isinstance(quantità, (int, float)):
            return jsonify({'error': 'Il campo "quantità" deve essere un numero.'}), 400

        with conn.cursor() as cursor:
            # Controlla se l'articolo è presente nell'inventario
            cursor.execute("SELECT 1 FROM current_inventory WHERE articolo = %s;", (articolo,))
            item_in_inventory = cursor.fetchone()
            
            # Imposta il valore di inCurrentInventory
            in_current_inventory = True if item_in_inventory else False

            # Controlla se l'articolo esiste già nella lista mustBe
            cursor.execute("SELECT quantità FROM mustbe WHERE articolo = %s;", (articolo,))
            result = cursor.fetchone()

            if result:
                # Se l'articolo esiste, somma la nuova quantità alla quantità esistente
                nuova_quantità = result[0] + quantità
                cursor.execute(
                    """
                    UPDATE mustbe 
                    SET quantità = %s, inCurrentInventory = %s
                    WHERE articolo = %s;
                    """,
                    (nuova_quantità, in_current_inventory, articolo)
                )
                conn.commit()
                message = 'Quantità aggiornata con successo'
            else:
                # Se l'articolo non esiste, aggiungi un nuovo articolo a mustBe
                cursor.execute(
                    """
                    INSERT INTO mustbe (articolo, quantità, inCurrentInventory) 
                    VALUES (%s, %s, %s);
                    """,
                    (articolo, quantità, in_current_inventory)
                )
                conn.commit()
                message = 'Articolo aggiunto con successo'

            if not item_in_inventory:
                # Se l'articolo non è nell'inventario, aggiungilo alla shopping list
                cursor.execute(
                    "INSERT INTO shopping_list (articolo, quantità) VALUES (%s, %s);",
                    (articolo, quantità)
                )
                conn.commit()
                message += ' e aggiunto alla shopping list.'

        return jsonify({'message': message}), 200

    except Exception as error:
        return jsonify({'error': str(error)}), 500

def update_mustBe_item(conn, articolo, updated_item):
    try:
        quantità = updated_item.get('quantità')

        if quantità is None or not isinstance(quantità, (int, float)):
            return jsonify({'error': 'Il campo "quantità" deve essere un numero.'}), 400

        with conn.cursor() as cursor:
            # Controlla se l'articolo esiste già nella lista mustBe
            cursor.execute("SELECT quantità FROM mustbe WHERE articolo = %s;", (articolo,))
            result = cursor.fetchone()

            if not result:
                return jsonify({'error': f'Articolo {articolo} non trovato nella lista mustBe.'}), 404

            # Quantità attuale in mustbe
            quantità_attuale = result[0]

            # Controlla se l'articolo è presente nell'inventario
            cursor.execute("SELECT 1 FROM current_inventory WHERE articolo = %s;", (articolo,))
            item_in_inventory = cursor.fetchone()
            in_current_inventory = True if item_in_inventory else False

            # Rimuovi dallla shopping_list se la nuova quantità è inferiore alla quantità attuale in inventario
            if quantità < quantità_attuale:
                cursor.execute("DELETE FROM shopping_list WHERE articolo = %s;", (articolo,))

            # Aggiorna la quantità dell'articolo
            cursor.execute(
                """
                UPDATE mustbe 
                SET quantità = %s, inCurrentInventory = %s
                WHERE articolo = %s;
                """,
                (quantità, in_current_inventory, articolo)
            )
            conn.commit()
            return jsonify({'message': f'Articolo {articolo} aggiornato con successo'}), 200

    except Exception as error:
        return jsonify({'error': str(error)}), 500


def delete_mustBe_item(conn, articolo):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM mustbe WHERE articolo = %s;", (articolo,)
            )
            conn.commit()
            return jsonify({'message': f'Articolo {articolo} eliminato con successo'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 500