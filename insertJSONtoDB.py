import json
import psycopg2

# Conectar a tu base de datos
conn = psycopg2.connect(
    dbname="hskify",
    user="diego",
    password="password",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

"""
# Cargar el JSON desde un archivo (o puedes adaptarlo para usar una variable)
with open('hsk-level-1.json', 'r') as file:
    characters = json.load(file)

    # Preparar y ejecutar la consulta SQL para insertar datos
    insert_query = '''
    INSERT INTO Characters (CharacterID, Hanzi, Pinyin, StrokeCount, Translation, HSKLevel)
    VALUES (%s, %s, %s, %s, %s, %s);
    '''
    
    for character in characters:
        # Combinar las traducciones en una sola cadena separada por comas
        translations = ", ".join(character['translations'])
        data_tuple = (character['id'], character['hanzi'], character['pinyin'], character['trazos'], translations, character['hsklevel'])
        cursor.execute(insert_query, data_tuple)
    
"""

with open('json/hsk-level-1-sentences.json', 'r', encoding='utf-8') as file:
    sentences = json.load(file)

insert_query = """
    INSERT INTO ExampleSentences (CharacterID, Sentence, Translation)
    VALUES (%s, %s, %s);
    """

# Insertar cada oración en la base de datos
for sentence in sentences:
    data_tuple = (sentence['characterid'], sentence['sentence'], sentence['translation'])
    cursor.execute(insert_query, data_tuple)

# Guardar los cambios y cerrar la conexión
conn.commit()
cursor.close()
conn.close()
