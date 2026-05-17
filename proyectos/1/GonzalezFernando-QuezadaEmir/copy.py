# En este archivo se lleva a cabo la "extracción" de un archivo dentro de Fiunamfs.img
# para después "guardarlo" en el sistema de archivos del host (nuestro sistema operativo).
# O en pocas palabras, se copia un archivo desde Fiunamfs.img a nuestro sistema operativo.

from pathlib import Path
import sys
import struct
from reader import superbloque, directorio, analizar 
# Importamos las funciones superbloque y directorio 
# desde  reader.py para reutilizar el código de análisis 
# del sistema de archivos Fiunamfs.


# def extract_file(path_img, file_name, path_output):

superbloque_info = analizar("fiunamfs.img") # Obtenemos la información del superbloque.
print(superbloque_info) # Imprimimos la información del superbloque para verificar que se ha leído correctamente.
     