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
        sync_shopping_list(conn)  # Aggiorna la lista della spesa
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    mustbe.articolo, 
                    mustbe.quantità,
                    mustbe.unità_misura,
                    COALESCE(current_inventory.quantità, 0) AS inventory_quantità,
                    (COALESCE(current_inventory.quantità, 0) >= mustbe.quantità) AS inCurrentInventory
                FROM mustbe
                LEFT JOIN current_inventory 
                ON mustbe.articolo = current_inventory.articolo;
            """)
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            inventory = [dict(zip(colnames, row)) for row in rows]
            return jsonify(inventory)
    except Exception as error:
        return jsonify({'error': str(error)}), 500

def add_mustBe_item(conn, new_item):
    try:
        articolo = new_item.get('articolo')
        quantità = new_item.get('quantità')
        unità_misura = new_item.get('unità_misura')  # Aggiungi il campo unità_misura

        if not articolo or not isinstance(articolo, str):
            return jsonify({'error': 'Il campo "articolo" deve essere una stringa e non può essere vuoto.'}), 400

        if quantità is None or not isinstance(quantità, (int, float)):
            return jsonify({'error': 'Il campo "quantità" deve essere un numero.'}), 400

        if not unità_misura or not isinstance(unità_misura, str):
            return jsonify({'error': 'Il campo "unità_misura" deve essere una stringa e non può essere vuoto.'}), 400

        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM current_inventory WHERE articolo = %s;", (articolo,))
            item_in_inventory = cursor.fetchone()
            in_current_inventory = True if item_in_inventory else False

            cursor.execute("SELECT quantità FROM mustbe WHERE articolo = %s;", (articolo,))
            result = cursor.fetchone()

            if result:
                nuova_quantità = result[0] + quantità
                cursor.execute(
                    """
                    UPDATE mustbe 
                    SET quantità = %s, inCurrentInventory = %s, unità_misura = %s  -- Aggiungi il campo unità_misura
                    WHERE articolo = %s;
                    """,
                    (nuova_quantità, in_current_inventory, unità_misura, articolo)
                )
                conn.commit()
                message = 'Quantità aggiornata con successo'
            else:
                cursor.execute(
                    """
                    INSERT INTO mustbe (articolo, quantità, inCurrentInventory, unità_misura) 
                    VALUES (%s, %s, %s, %s);
                    """,
                    (articolo, quantità, in_current_inventory, unità_misura)  # Aggiungi il campo unità_misura
                )
                conn.commit()
                message = 'Articolo aggiunto con successo'

            if not item_in_inventory:
                cursor.execute(
                    "INSERT INTO shopping_list (articolo, quantità, unità_misura) VALUES (%s, %s, %s);",
                    (articolo, quantità, unità_misura)  # Assicurati di passare unità_misura qui
                )
                conn.commit()
                message += ' e aggiunto alla shopping list.'

        return jsonify({'message': message}), 200

    except Exception as error:
        return jsonify({'error': str(error)}), 500

def get_mustBeItems(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    mustbe.articolo, 
                    mustbe.quantità,
                    mustbe.unità_misura,  -- Aggiungi il campo unità_misura
                    COALESCE(current_inventory.quantità, 0) AS inventory_quantità,
                    (COALESCE(current_inventory.quantità, 0) >= mustbe.quantità) AS inCurrentInventory
                FROM mustbe
                LEFT JOIN current_inventory 
                ON mustbe.articolo = current_inventory.articolo;
            """)
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            inventory = [dict(zip(colnames, row)) for row in rows]

            # Cicla su ogni articolo per verificare se deve essere aggiunto o rimosso dalla shopping list
            for item in inventory:
                articolo = item['articolo']
                quantità = item['quantità']
                unità_misura = item['unità_misura']  # Aggiungi unità_misura
                inventory_quantità = item['inventory_quantità']
                
                if inventory_quantità >= quantità:
                    cursor.execute("DELETE FROM shopping_list WHERE articolo = %s;", (articolo,))
                    conn.commit()
                else:
                    quantità_mancante = quantità - inventory_quantità
                    cursor.execute("SELECT quantità FROM shopping_list WHERE articolo = %s;", (articolo,))
                    result = cursor.fetchone()

                    if result:
                        if result[0] < quantità_mancante:
                            nuova_quantità = result[0] + quantità_mancante
                            cursor.execute(
                                "UPDATE shopping_list SET quantità = %s WHERE articolo = %s;",
                                (nuova_quantità, articolo)
                            )
                    else:
                        cursor.execute(
                            "INSERT INTO shopping_list (articolo, quantità, unità_misura) VALUES (%s, %s, %s);",
                            (articolo, quantità_mancante, unità_misura)  # Aggiungi unità_misura qui
                        )
                    conn.commit()

            return jsonify(inventory)
    except Exception as error:
        return jsonify({'error': str(error)}), 500

def update_mustBe_item(conn, articolo, updated_item):
    try:
        quantità = updated_item.get('quantità')
        unità_misura = updated_item.get('unità_misura')  # Aggiungi il campo unità_misura

        if quantità is None or not isinstance(quantità, (int, float)):
            return jsonify({'error': 'Il campo "quantità" deve essere un numero.'}), 400

        with conn.cursor() as cursor:
            cursor.execute("SELECT quantità FROM mustbe WHERE articolo = %s;", (articolo,))
            result = cursor.fetchone()

            if not result:
                return jsonify({'error': f'Articolo {articolo} non trovato nella lista mustBe.'}), 404

            quantità_attuale = result[0]

            cursor.execute("SELECT 1 FROM current_inventory WHERE articolo = %s;", (articolo,))
            item_in_inventory = cursor.fetchone()
            in_current_inventory = True if item_in_inventory else False

            if quantità < quantità_attuale:
                cursor.execute("DELETE FROM shopping_list WHERE articolo = %s;", (articolo,))

            cursor.execute(
                """
                UPDATE mustbe 
                SET quantità = %s, inCurrentInventory = %s, unità_misura = %s  -- Aggiungi il campo unità_misura
                WHERE articolo = %s;
                """,
                (quantità, in_current_inventory, unità_misura, articolo)  # Aggiungi il campo unità_misura
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
    
def sync_shopping_list(conn):
    """Sincronizza la lista della spesa in base agli articoli di 'mustbe' e 'added_items'."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    mustbe.articolo, 
                    mustbe.quantità,
                    mustbe.unità_misura,
                    COALESCE(current_inventory.quantità, 0) AS inventory_quantità
                FROM mustbe
                LEFT JOIN current_inventory 
                ON mustbe.articolo = current_inventory.articolo;
            """)
            rows = cursor.fetchall()
            for row in rows:
                articolo, quantità, unità_misura, inventory_quantità = row
                if inventory_quantità >= quantità:
                    cursor.execute("DELETE FROM shopping_list WHERE articolo = %s;", (articolo,))
                else:
                    quantità_mancante = quantità - inventory_quantità
                    cursor.execute("SELECT quantità FROM shopping_list WHERE articolo = %s;", (articolo,))
                    result = cursor.fetchone()
                    if result:
                        if result[0] < quantità_mancante:
                            nuova_quantità = result[0] + quantità_mancante
                            cursor.execute(
                                "UPDATE shopping_list SET quantità = %s WHERE articolo = %s;",
                                (nuova_quantità, articolo)
                            )
                    else:
                        cursor.execute(
                            "INSERT INTO shopping_list (articolo, quantità, unità_misura) VALUES (%s, %s, %s);",
                            (articolo, quantità_mancante, unità_misura)
                        )

            # Sincronizzazione per gli articoli nella tabella added_items
            cursor.execute("SELECT * FROM added_items;")
            added_rows = cursor.fetchall()
            for added_row in added_rows:
                articolo, quantità, unità_misura = added_row[0], added_row[1], added_row[2]
                cursor.execute(
                    "INSERT INTO shopping_list (articolo, quantità, unità_misura) VALUES (%s, %s, %s) "
                    "ON CONFLICT (articolo) DO UPDATE SET quantità = shopping_list.quantità + EXCLUDED.quantità;",
                    (articolo, quantità, unità_misura)
                )

            conn.commit()
    except Exception as error:
        print(f'Errore nella sincronizzazione della shopping list: {error}')

