import json

import psycopg2

# Conectar a tu base de datos
conn = psycopg2.connect(dbname='hskify', user='diego', password='password', host='localhost', port='5432')
cursor = conn.cursor()


with open('json/hsk-level-1-sentences.json', encoding='utf-8') as file:
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
