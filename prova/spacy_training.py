import json
import spacy
from spacy.training import Example
from pathlib import Path
from spacy.training import offsets_to_biluo_tags

def auto_correct_offsets(training_data):
    corrected_data = []
    for item in training_data:
        text = item['text']
        corrected_entities = []
        for start, end, label in item['entities']:
            # Trova il testo dell'entità e ricalcola la posizione
            entity_text = text[start:end]
            actual_start = text.find(entity_text)
            actual_end = actual_start + len(entity_text)
            if actual_start != -1:
                corrected_entities.append([actual_start, actual_end, label])
        corrected_data.append({"text": text, "entities": corrected_entities})
    return corrected_data

def validate_training_data(nlp, training_data):
    for item in training_data:
        if not isinstance(item, dict):
            print(f"Errore: l'elemento {item} non è un dizionario.")
            continue
        if 'text' not in item or 'entities' not in item:
            print(f"Errore: l'elemento {item} non contiene i campi richiesti ('text' e 'entities').")
            continue
        doc = nlp.make_doc(item['text'])
        try:
            entities = item['entities']
            offsets_to_biluo_tags(doc, entities)
        except Exception as e:
            print(f"Errore nel record: {item}")
            print(f"Errore: {e}")

def train_spacy_model(training_data_path, output_dir):
    # Carica i dati di training dal file JSON
    with open(training_data_path, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    # Correggi gli offset nei dati di training
    training_data = auto_correct_offsets(training_data)
    
    # Valida i dati di training
    nlp = spacy.blank("it")  # Crea un modello vuoto prima della validazione
    validate_training_data(nlp, training_data)

    # Imposta il numero di iterazioni in base al numero di record
    n_iter = len(training_data)
    print(f"Numero di iterazioni impostato su: {n_iter}")

    # Aggiungi il componente NER (Named Entity Recognition) al pipeline
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")
    
    # Aggiungi le etichette presenti nel dataset al componente NER
    for item in training_data:
        for ent in item['entities']:
            label = ent[2]
            print(f"Aggiunta etichetta: {label}")  # Stampa la label aggiunta
            ner.add_label(label)
    
    # Disabilita altri componenti del pipeline per velocizzare l'addestramento
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()
        for iter in range(n_iter):
            print(f"Iterazione {iter+1}/{n_iter}")
            losses = {}
            examples = []
            for item in training_data:
                doc = nlp.make_doc(item['text'])
                entities = [(start, end, label) for start, end, label in item['entities']]
                examples.append(Example.from_dict(doc, {"entities": entities}))
                
                # Stampa le entità aggiunte per questa iterazione
                print(f"Testo: {item['text']}")
                print(f"Entità: {entities}")
            
            # Addestramento effettivo
            nlp.update(
                examples,
                drop=0.35,  # Tasso di dropout
                losses=losses,
            )
            print("Losses:", losses)

    # Salva il modello addestrato
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_path)
    print(f"Modello salvato in {output_path}")
    
    # Verifica del modello con una frase di test
    print("\nVerifica del modello:")
    test_sentence = "ho mangiato una carota"
    doc = nlp(test_sentence)
    for ent in doc.ents:
        print(f"Entità rilevata: {ent.text} -> {ent.label_}")



if __name__ == "__main__":
    # Percorso del file di training e directory di output
    TRAINING_DATA_PATH = "training_data.json"
    OUTPUT_DIR = "./inventory_model"
    # Avvia l'addestramento
    train_spacy_model(TRAINING_DATA_PATH, OUTPUT_DIR)
