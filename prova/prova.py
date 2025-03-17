import speech_recognition as sr
import spacy

# Carica il modello personalizzato
nlp = spacy.load("./inventory_model")

# Mappatura delle parole a numeri
word_to_number = {
    "una": 1,
    "due": 2,
    "tre": 3,
    "quattro": 4,
    "cinque": 5,
    "sei": 6,
    "sette": 7,
    "otto": 8,
    "nove": 9,
    "dieci": 10
}

# Funzione per interpretare i comandi usando il modello personalizzato
def interpret_command(command):
    doc = nlp(command)
    
    # Mappa dei verbi per azioni del database
    action_map = {
        "comprato": "insert",
        "acquistato": "insert",
        "mangiato": "delete",
        "consumato": "delete"
    }

    # Rileva l'azione (ad esempio, "insert" o "delete") in base ai verbi
    action = None
    for verb in action_map:
        if verb in command:
            action = action_map[verb]
            break
    
    if not action:
        action = "unknown"

    # Estrai l'oggetto (ITEM) e la quantità
    item = [ent.text for ent in doc.ents if ent.label_ == "ITEM"]
    print(item)
    quantity_word = [ent.text for ent in doc.ents if ent.label_ == "QUANTITY"]
    
    # Se la quantità è espressa come parola (ad esempio "una"), convertila in numero
    quantity = 1  # Default: 1 se non è specificata una quantità
    if quantity_word:
        word = quantity_word[0].lower()
        quantity = word_to_number.get(word, 1)  # Se la parola non è nel dizionario, usa 1
    
    return action, item[0] if item else "sconosciuto", quantity

# Funzione principale per l'ascolto del comando vocale
def main():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Parla ora... (es. 'ho mangiato una carota')")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.energy_threshold = 4000  # Aumenta il valore se il riconoscimento è troppo sensibile al rumore di fondo
        
        while True:  # Ciclo continuo per ascoltare e interpretare i comandi
            try:
                # Ascolta in continuo
                audio_data = recognizer.listen(source)
                print("Riconoscimento in corso...")
                
                # Converti l'audio in testo
                command = recognizer.recognize_google(audio_data, language="it-IT")
                print("Hai detto:", command)
                
                # Interpreta il comando
                action, item, quantity = interpret_command(command)
                print(f"Azione: {action} {quantity} {item}")
            
            except sr.UnknownValueError:
                print("Non ho capito cosa hai detto. Riprova.")
            except sr.RequestError as e:
                print(f"Errore del servizio di riconoscimento vocale: {e}")

# Esegui il programma
if __name__ == "__main__":
    main()
