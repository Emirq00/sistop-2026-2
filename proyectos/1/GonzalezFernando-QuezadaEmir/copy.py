# En este archivo se lleva a cabo la "extracción" de un archivo dentro de Fiunamfs.img
# para después "guardarlo" en el sistema de archivos del host (nuestro sistema operativo).
# O en pocas palabras, se copia un archivo desde Fiunamfs.img a nuestro sistema operativo.

from pathlib import Path
import sys
import struct
from reader import superbloque, directorio, analizar, imprimir_archivos
# Importamos las funciones superbloque y directorio 
# desde  reader.py para reutilizar el código de análisis 
# del sistema de archivos Fiunamfs.

def find_file(data, filename, superbloque_info):
    # En esta función buscamos un archivo específico dentro del directorio de Fiunamfs.img,
    # utilizando la información del superbloque para entender cómo está estructurado 
    # el sistema de archivos.

    # Args:
        # data: Contenido del archivo .img leído en bytes.
        # filename: El nombre del archivo que queremos encontrar dentro de Fiunamfs.img
        # superbloque_info: Un diccionario con la información del superbloque, 
        # que incluye el tamaño de los clusters y la ubicación del directorio raíz.

    # Returns:
        # Diccionario con la información del archivo encontrado (tamaño, primer cluster, etc.) 
        # o None si el archivo no se encuentra.
    
    cluster_size = superbloque_info['cluster_size']
    dir_clusters = superbloque_info['num_clusters']

    # Recordemos que el directorio empieza en el cluster 1.
    dir_start = cluster_size
    dir_size = dir_clusters * cluster_size
    dir_data = data[dir_start:dir_start + dir_size]

    # Cada entrada mide 64 bytes
    entry_size = 64
    num_entries = dir_size // entry_size

    # Comenzamos a iterar sobre las diferentes entradas, hasta encontrar el archivo
    # o hasta terminar de revisar todas las entradas del directorio.
    for i in range(num_entries):
        entry_start = i * entry_size
        entry_data = dir_data[entry_start:entry_start + entry_size]
        
        # Byte 0: Tipo de archivo
        file_type = chr(entry_data[0])
        
        # Saltamos a otra entrada, si el archivo está vacío
        if file_type == '/':
            continue
        
        # Bytes 1-15: Nombre del archivo
        entry_filename = entry_data[1:16].decode('ascii', errors='ignore').rstrip('\x00').rstrip()
        
        # ¿Es el archivo que buscamos?
        if entry_filename == filename:
            # Bytes 16-19: Tamaño del archivo
            file_size = struct.unpack('<I', entry_data[16:20])[0]
            
            # Bytes 20-23: Cluster inicial
            start_cluster = struct.unpack('<I', entry_data[20:24])[0]
            
            # Bytes 24-38: Fecha de creación
            creation_time = entry_data[24:39].decode('ascii', errors='ignore').rstrip('\x00')
            
            # Bytes 40-54: Fecha de modificación
            modification_time = entry_data[40:55].decode('ascii', errors='ignore').rstrip('\x00')
            
            return {
                'filename': entry_filename,
                'size': file_size,
                'start_cluster': start_cluster,
                'creation_time': creation_time,
                'modification_time': modification_time,
                'entry_index': i
            }
    
    return None



def extraer(data, filename, nombre_salida=None):
	# Args:
        # filename: El nombre del archivo que queremos extraer de Fiunamfs.img
        # nombre_salida: Nombre con el que queremos guardar el archivo extraído 
        # en nuestro sistema operativo.
        # data: El contenido del archivo .img leído en bytes.
        
    # Returns: 
        # True si la extracción fue exitosa. False si falló.
	
    superbloque_info = superbloque(data) # Obtenemos la información del superbloque.
    cluster_size = superbloque_info['cluster_size']

    file_info = find_file(data, filename, superbloque_info)  

    if file_info is None:
        print(f"Error: Archivo '{filename}' no encontrado en el sistema de archivos")
        return False

    print(f"¡Archivo encontrado!")
    print(f"Tamaño: {file_info['size']} bytes")
    print(f"Cluster inicial: {file_info['start_cluster']}")
    print(f"Creado: {file_info['creation_time']}")
    print(f"Modificado: {file_info['modification_time']}")
    
    # Calculamos la posición en bytes donde empiezan los datos que buscamos
    # Fórmula: cluster × tamaño_del_cluster
    data_start = file_info['start_cluster'] * cluster_size
    data_end = data_start + file_info['size']

    # Extraemos los bytes correspondientes al archivo que queremos copiar.
    file_data = data[data_start:data_end]

    # Checamos que la cantidad de bytes sea la correcta.
    if len(file_data) != file_info['size']:
        print(f"Advertencia: Se esperaban {file_info['size']} bytes, " f"pero se leyeron {len(file_data)} bytes")

    if nombre_salida is None:
        nombre_salida = filename
    
    output_file = Path(nombre_salida)

    # Puede pasar que el archivo ya exista, así que preguntamos al usuario si desea sobrescribirlo.
    if output_file.exists():
        response = input(f"El archivo '{nombre_salida}' ya existe. ¿Sobrescribir? (s/n): ")
        if response.lower() != 's':
            print("Operación cancelada")
            return False
        

    # Escribimos el archivo (copiamos de Fiunamfs.img a nuestro sistema operativo).
    try:
        with open(nombre_salida, 'wb') as f:
            f.write(file_data)
        
        print(f"Archivo extraído exitosamente a: {nombre_salida}")
        print(f"Tamaño: {len(file_data)} bytes")
        return True
        
    except Exception as e:
        print(f"Error al escribir el archivo: {e}")
        return False

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
    arg1 = "logo.png" # El nombre del archivo que queremos extraer de Fiunamfs.img
    arg2 = "logo_extraido.png" # Nombre con el que queremos guardar el archivo

    extraer(data, arg1, arg2)


if __name__ == "__main__":
    main()
    





     
    