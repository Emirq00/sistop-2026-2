from pathlib import Path
import sys # Libreria para el uso de las funciones del sistema como sys.argv

import struct # Libreria para trabajar con datos binarios, 
			  # permite convertir entre bytes y tipos de datos de Python.

def superbloque(data):
	# En la función superbloque leemos y parseamos el superbloque de nuestro fiunamfs.img
	# Recordemos que en el superbloque tenemos datos de identificacion 

	print("="*60)
	print("Análisis del Superbloque")
	print("="*60)
	
	id_bytes = data[0:4].hex()	
	print(f"Bytes de identificacion: {id_bytes}")
	# .hex() convierte los bytes a una representación hexadecimal, 
	# lo que facilita la lectura y comparación de los datos binarios.
	
	fileName = data[5:13].decode('ascii', errors='ignore').rstrip('\x00')
	# Decodificamos los bytes 5-13 a texto usando ASCII, ignorando errores y eliminando 
	# los caracteres nulos al final.
	print(f"Sistema de archivos: {fileName}")

	version = data[14:18].decode('ascii', errors='ignore').rstrip('\x00')
	print(f"Version del sistema de archivos: {version}")
	# Nuevamente aplicamos una decodificación similar para obtener la versión del sistema de archivos.

	volumen = data[20:35].decode('ascii', errors='ignore').rstrip('\x00')
	print(f"Nombre del volumen: {volumen}")
	# De los bytes 20-36 obtenemos el nombre del volumen, aplicando el mismo proceso.

	cluster_size = struct.unpack('<I', data[40:44])[0] 
	# "<" = Little-endian
    # "I" = Entero 4 bytes (ID)
    # "H" = Entero 2 bytes (Versión)
	print(f"Tamaño del cluster: {cluster_size} bytes") # type: ignore
	# Para obtener el tamaño del cluster, utilizamos struct.unpack con el formato '<I', 
	# que indica que queremos interpretar los bytes como un entero sin signo de 4 bytes en
	# formato little-endian. El resultado es una tupla, por lo que accedemos al primer elemento con [0].

def analizar(nombre):
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
		superbloque(f.read())		

	print("Analisis completo")

if __name__ == "__main__":
	analizar(sys.argv[1]) 

# argv[0] -> Nombre del script de python (reader.py)
# argv[1] -> Nombre del .img que (fiunamfs.img)


	
