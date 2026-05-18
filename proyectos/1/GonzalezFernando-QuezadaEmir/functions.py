import struct # Libreria para trabajar con datos binarios, 
			  # permite convertir entre bytes y tipos de datos de Python.


def directorio(data, infoSuperbloque):
	
	# En esta función leemos el directorio de nuestro fiunamfs.img
	
    # Args:
        # data: Contenido del archivo .img leído en bytes.
        # infoSuperbloque: Un diccionario con la información del superbloque,
        # que incluye el tamaño de los clusters y la ubicación del directorio raíz. 
	
    # Returns:
        # Una lista de archivos encontrados en el directorio, con su información relevante 
        # (nombre, tamaño, etc.).
		
	cluster_size = infoSuperbloque['cluster_size']
	num_clusters = infoSuperbloque['num_clusters']

	start = cluster_size # Como sabemos que el cluster 0 es el superbloque, 
						 # el directorio comienza en el cluster 1. 
	
	dir_size = num_clusters * cluster_size # Calculamos el tamaño total del directorio.

	end = start + (dir_size) # El directorio ocupa un número de clusters, 
												# por lo que calculamos el final sumando el tamaño 
												# total del directorio al inicio.
	
	infoDirectorio = data[start:end] # Obtenemos los bytes correspondientes al directorio.
	entry_size = 64 # Cada entrada del directorio ocupa 64 bytes.

	num_entries=dir_size//entry_size # Calculamos el número de entradas dividiendo 
									 # el tamaño total del directorio entre el tamaño 
									 # de cada entrada.

	files= [] # Lista para almacenar la información de los archivos ocupados encontrados en el directorio.

	for i in range(num_entries):
		entry_start = i * entry_size
		entry_data = infoDirectorio[entry_start:entry_start + entry_size] # Bytes de la entrada actual.
		file_type = chr(entry_data[0]) # El primer byte indica el tipo de archivo (-, /).
		if file_type=="-":
			files.append(entry_data) # Si el tipo de archivo es "-", lo consideramos un archivo regular y 
									 # lo agregamos a la lista de archivos.
	
	return files # Devolvemos la lista de archivos encontrados en el directorio.

def superbloque(data):
	# En la función superbloque leemos y parseamos el superbloque de nuestro fiunamfs.img
	# Recordemos que en el superbloque tenemos datos de identificacion del sistema 
	# de archivos, como el tamaño de los clusters, el número de clusters que mide el directorio, etc.

	# Args:
        # data: Contenido del archivo .img leído en bytes.
	
    # .hex() convierte los bytes a una representación hexadecimal, 
	# lo que facilita la lectura y comparación de los datos binarios.
	id_bytes = data[0:4].hex()	
	
	
    # Decodificamos los bytes 5-13 a texto usando ASCII, ignorando errores y eliminando 
	# los caracteres nulos al final.
	fileName = data[5:13].decode('ascii', errors='ignore').rstrip('\x00')
	
    # Versión del sistema de archivos, obtenida de los bytes 14-18, decodificada de manera 
    # similar al nombre del volumen.
	version = data[14:18].decode('ascii', errors='ignore').rstrip('\x00')


	# Nuevamente aplicamos una decodificación similar para obtener la versión del sistema de archivos.
	volumen = data[20:35].decode('ascii', errors='ignore').rstrip('\x00')
	

	# De los bytes 20-36 obtenemos el nombre del volumen, aplicando el mismo proceso.
	# "<" = Little-endian
    # "I" = Entero 4 bytes (ID)
	# Para obtener el tamaño del cluster, utilizamos struct.unpack con el formato '<I', 
	# que indica que queremos interpretar los bytes como un entero sin signo de 4 bytes en
	# formato little-endian. El resultado es una tupla, por lo que accedemos al primer elemento con [0].
	cluster_size = struct.unpack('<I', data[40:44])[0] 

    # De manera similar, obtenemos el número de clusters que mide el directorio
	# utilizando struct.unpack con el mismo formato.
	num_clusters = struct.unpack('<I', data[50:54])[0]
	

    # Nos indica el número total de clusters que tiene la unidad completa.
	clusters_unidad = struct.unpack('<I', data[60:64])[0]
	

	return {'id_bytes': id_bytes, 
		 	'fileName': fileName, 
			'version': version, 
			'volumen': volumen, 
			'cluster_size': cluster_size, 
			'num_clusters': num_clusters, 
			'clusters_unidad': clusters_unidad}


def imprimir_archivos(files):
		# La función imprimir archivos nos decodifica las entradas del directorio, 
		# brindandonos información sobre los archivos almacenados.

		# Args:
			# files: Lista de archivos encontrados en el directorio, con su información relevante.

		for entry_data in files:
			file_type = chr(entry_data[0]) # El primer byte indica el tipo de archivo (-, /).	
			file_name = entry_data[1:15].decode('ascii', errors='ignore').rstrip('\x00') # Bytes 1-15 para el nombre del archivo.
			# Bytes 16-20 para el tamaño del archivo.
			file_size = struct.unpack('<I', entry_data[16:20])[0] 

			# Bytes 20-23 para el primer cluster del archivo.
			first_cluster = struct.unpack('<I', entry_data[20:24])[0] 

			# Bytes 24-32 para la fecha de creación.
			creation_time = entry_data[24:44].decode('ascii', errors='ignore').rstrip('\x00')

			# Bytes 40-55 para la fecha de modificación.
			modification_time = entry_data[44:64].decode('ascii', errors='ignore').rstrip('\x00')
			print(f"Archivo: {file_name}")
			print(f"  Tipo: {file_type}")
			print(f"  Tamaño: {file_size} bytes")
			print(f"  Primer cluster: {first_cluster}")
			print(f"  Fecha de creación: {creation_time}")
			print(f"  Fecha de modificación: {modification_time}")
