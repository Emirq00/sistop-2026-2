from pathlib import Path
import sys # Libreria para el uso de las funciones del sistema como sys.argv
import struct
from functions import superbloque, directorio, imprimir_archivos



def read(nombre):
	filePath=Path(nombre)
	
	if not filePath.exists():
		print(f"El archivo {nombre} no existe :(")
		return 

	size = filePath.stat().st_size
	#Esperamos tener un tamaño de 1440 KB
	
	print("="*60)
	print(f"Análisis del archivo {nombre}")
	print("="*60)
	print(f"Tamaño del archivo: {size} bytes")
	print(f"Tamaño esperado: {1440*1024} bytes")

	if(size != 1440*1024):
		print("El tamaño no coincide ._.")
	
	# "with open ..." actúa como un context manager, cerrando el archivo automáticamente al finalizar.
	# ¿qué es un context manager? Es una estructura que permite gestionar recursos de manera eficiente, 
	# asegurando que se liberen correctamente, incluso si ocurre un error.

	with open(nombre, 'rb') as f: # r -> read, b -> binary, rb -> read binary
		data = f.read()

	infoSuperbloque = superbloque(data)

	entrys = directorio(data, infoSuperbloque)
	
	imprimir_archivos(entrys)

	print("Analisis completo")

if __name__ == "__main__":
	read(sys.argv[1]) 

# argv[0] -> Nombre del script de python (reader.py)
# argv[1] -> Nombre del .img que queremos analizar(fiunamfs.img)


	
