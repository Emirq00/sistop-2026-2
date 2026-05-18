# En este archivo se lleva a cabo la "extracción" de un archivo dentro de Fiunamfs.img
# para después "guardarlo" en el sistema de archivos del host (nuestro sistema operativo).
# O en pocas palabras, se copia un archivo desde Fiunamfs.img a nuestro sistema operativo.

from pathlib import Path
import sys
import struct
from functions import superbloque, directorio, imprimir_archivos, extraer
# Importamos las funciones superbloque y directorio 
# desde  reader.py para reutilizar el código de análisis 
# del sistema de archivos Fiunamfs.

def main():
    nombre = "fiunamfs.img" # Nombre del archivo .img que queremos analizar.
    with open(nombre, "rb") as f:  # r -> read, b -> binary, rb -> read binary
        data = f.read()
    superbloque_info = superbloque(data)
    lista = directorio(data, superbloque_info)
    # Listamos los archivos encontrados 
    imprimir_archivos(lista)
    # Argumentos para extraer
        # arg1: El nombre del archivo que queremos extraer de Fiunamfs.img
        # arg2: Nombre con el que queremos guardar el archivo extaído.
        # Nota: El archivo se guarda en el mismo directorio en el que nos encontramos, 
        # a menos que se especifique una ruta diferente en arg2.

    # Ejemplo:
    arg1 = "prueba.txt" # El nombre del archivo que queremos extraer de Fiunamfs.img
    arg2 = "prueba_extraida.txt" # Nombre con el que queremos guardar el archivo

    extraer(data, arg1, arg2)


if __name__ == "__main__":
    main()
    





     
    