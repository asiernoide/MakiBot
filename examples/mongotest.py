import pymongo

'''
Archivo de prueba para testear la conexión con MongoDB.
Este es un programa realizado suponiendo que se tiene una base de datos en MongoDB con una colección
llamada "danganronpa_characters" y que contiene documentos con la siguiente estructura:

{
    "_id": ObjectId("5f9e1b9b0b9b9b5j9b9b7x9b"),
    "name": "Maki Harukawa",
    "image": "https://i.imgur.com/9X9X9X9.png",
    "gender": "Female"
}

Disponer de una base de datos con estas características es necesario para el funcionamiento de los siguientes comandos de MakiBot:
- /drwaifu
- /drkmk

La URL de la base de datos, así como el nombre de la base de datos se pueden modificar en los
parámetros de la aplicación, y serán obtenidos a través de la variable de entorno "MONGODB_URI" y "MONGODB_DBNAME" respectivamente.

El nombre de las colecciones y su estructura debe ser similar a la presentada para los items
de todos los juegos/series para el correcto funcionamiento de los
comandos mencionados anteriormente. El nombre de las colecciones para cualquier búsqueda de items seguirá el siguiente formato:
- <nombre_del_juego>_<nombre_de_la_coleccion>

De todas formas pondré el nombre de la colección como comentario en cada comando que use una de estas para evitar confusiones.
'''

# Establecer conexión con MongoDB
client = pymongo.MongoClient('MONGODB_URI')

# Obtener base de datos
db = client["MONGODB_DBNAME"]

# Obtener colección
collection = db["danganronpa_characters"]

# Define los criterios de búsqueda
filter = {"gender": "Female"}

# Define la lista de operaciones de agregación
pipeline = [{"$match": filter}, {"$sample": {"size": 1}}]

# Ejecuta la consulta de agregación y obtén el documento aleatorio
random_character = collection.aggregate(pipeline)

# Obtén el primer elemento del objeto CommandCursor
random_character = next(random_character)

# Imprimir el documento
print(random_character)
