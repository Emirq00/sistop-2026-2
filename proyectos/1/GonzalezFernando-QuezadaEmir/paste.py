from pathlib import Path
import sys
import struct
from datetime import datetime
from math import ceil
from reader import superbloque, directorio

def occupied_clusters(archivos):
    # Esta función nos devuelve los numeros de clusters ocupados
    # Ejemplos: si algún archivo ocupa los clusters 9, 10 y 11, esta función nos regresa [9, 10, 11].

    # Args:
        # archivos: Lista de los archivos ocupados, con su información (tamaño, cluster inicial, etc.)

    ocupados = set()

    for archivo in archivos:
        start_cluster = struct.unpack('<I', archivo[20:24])[0] # Cluster inicial del archivo
        file_size = struct.unpack('<I', archivo[16:20])[0] # Tamaño del archivo en bytes

        # Un cluster mide 4 sectores de 512 bytes, es decir, 2048 bytes.
        cluster_size = 2048
        # Calculamos el número de clusters necesarios para almacenar el archivo, redondeando hacia arriba.
        clusters_necesarios = ceil(file_size / cluster_size)
        
        # Marcar todos los clusters ocupados por este archivo
        for i in range(clusters_necesarios):
            ocupados.add(start_cluster + i)

    return ocupados


def available_clusters(archivos, neededClusters, totalClusters):
    # Función que nos indica los clusters contiguos disponibles para almacenar un nuevo archivo.

    # Args:
        # archivos: Lista de los archivos existentes
        # neededClusters: Número de clusters necesarios para almacenar el nuevo archivo.
        # totalClusters: Número total de clusters disponibles en el sistema de archivos.
    
    # Returns:
        # Nos regresa el número del primer cluster disponible 

    # Recordemos que el cluster 0 es el superbloque, y los clusters 1-8
    # están ocupados por el directorio, por lo que el primer cluster disponible
    # para almacenar archivos es el cluster 9.
    start = 9

    ocupados = occupied_clusters(archivos)

    for j in range(start, totalClusters):
        # Verificar si hay espacio desde start hasta start+clusters_necesarios
        ok = True
        for i in range(neededClusters):
            if (j + i) in ocupados or (j + i) >= totalClusters:
                ok = False
                break
        
        if ok:
            return j  # Encontramos espacio! Y retornamos el número del primer cluster disponible.
    
    return None  # No hay espacio suficiente

def find_directory_entry(data, superbloque_info):
    # Función dedicada a encontrar la primera entrada vacía en el directorio, para poder 
    # mapear el nuevo archivo.

    # Args:
        # data: Contenido del archivo .img leído en bytes.
        # superbloque_info: Diccionario con la información del superbloque, 
        # que incluye el tamaño de los clusters y la ubicación del directorio raíz.
    
    # Returns:
        # El número de la entrada vacía encontrada, o None si no hay entradas vacías D:

    cluster_size = superbloque_info['cluster_size']
    dir_clusters = superbloque_info['num_clusters']

    dir_start = cluster_size
    dir_size = dir_clusters * cluster_size
    dir_data = data[dir_start:dir_start + dir_size]
    entry_size = 64
    num_entries = dir_size // entry_size

    for i in range(num_entries):
        entry_start = i * entry_size
        entry_data = dir_data[entry_start:entry_start + entry_size]
        
        # Byte 0: Tipo de archivo
        file_type = chr(entry_data[0])
        
        # Si el tipo de archivo es '/', consideramos esta entrada como vacía.
        if file_type == '/':
            return i  # Retornamos el número de la entrada vacía encontrada.
        
    return None  # No hay entradas vacías disponibles.

def copy(img_path, archivo_local, nombre_destino=None):
    # Función principal para copiar un archivo desde el sistema de archivos local al sistema 
    # de archivos Fiunamfs.

    # Args:
        # img_path: Ruta al archivo .img de Fiunamfs.  
        # archivo_local: Ruta al archivo local que queremos copiar dentro de Fiunamfs.
        # nombre_destino: Nombre que queremos darle al archivo dentro de Fiunamfs. 
        # Si no se especifica, se usará el mismo nombre del archivo local.

    # Returns:
        # Un mensaje indicando el resultado de la operación (éxito o error).    
    
    # Primero validamos que el archivo local existe
    local_file = Path(archivo_local)
    if not local_file.exists():
        print(f"¡Error! El archivo local '{archivo_local}' no existe")
        return False
    
    # Leemos el contenido del archivo local
    with open(archivo_local, 'rb') as f:
        contenido_local = f.read()
    
    # Determinamos el nombre de destino
    if nombre_destino is None:
        nombre_destino = local_file.name
    
    img_file = Path(img_path)

    if not img_file.exists():
        print(f"ERROR! El archivo '{img_path}' no existe :()")
        return False

    with open(img_path, 'rb') as f:
        data = bytearray(f.read()) 
    
    superbloque_info = superbloque(data)

    if superbloque_info['fileName'] != 'FiUnamFS':
        print(f"ERROR! No es un sistema FiUnamFS válido")
        return False
    
    cluster_size = superbloque_info['cluster_size']
    total_clusters = superbloque_info['clusters_unidad']

    tamaño_archivo = len(contenido_local)

    # Calculamos el número de clusters necesarios para almacenar el nuevo archivo.
    clusters_necesarios = ceil(tamaño_archivo / cluster_size)
    print(f"Clusters necesarios: {clusters_necesarios}")

    archivos = directorio(data, superbloque_info)

    # Hacemos una verificación, para evitar errores de sobreescritura.
    for archivo in archivos:
        file_name = archivo[1:15].decode('ascii', errors='ignore').rstrip('\x00')
        if file_name == nombre_destino:
            response = input(f"El archivo '{nombre_destino}' ya existe en FiUnamFS. ¿Sobrescribir? (y/n): ")
            if response.lower() != 'y':
                print("¡Operación cancelada!")
                return False
            # TO DO mejora: Podríamos implementar sobrescritura marcando el viejo como eliminado
            print("Nota: La sobrescritura creará una nueva entrada (el archivo viejo quedará marcado)")
            break
    
    entrada_libre = find_directory_entry(data, superbloque_info)

    if entrada_libre is None:   
        print("¡Error! No hay entradas libres en el directorio para mapear el nuevo archivo.")
        return False   
    
    print(f"Entrada libre encontrada: #{entrada_libre}")

    primer_cluster = available_clusters(archivos, clusters_necesarios, total_clusters)

    if primer_cluster is None:
        print(f"ERROR! No hay suficiente espacio contiguo en el sistema de archivos")
        print(f"Se necesitan {clusters_necesarios} clusters consecutivos")
        return False
    
    print(f"Clusters libres encontrados: {primer_cluster} a {primer_cluster + clusters_necesarios - 1}")

    print(f"Escribiendo datos en clusters...")
    posicion_datos = primer_cluster * cluster_size

    # Escribimos el contenido del archivo local en el área de datos del sistema de archivos,
    # comenzando desde el cluster disponible que encontramos.
    data[posicion_datos:posicion_datos + tamaño_archivo] = contenido_local

    print(f"{tamaño_archivo} bytes escritos en posición {posicion_datos}")
    print(f"Actualizando la entrada del directorio...")

    # Calculamos la posición de la entrada en el directorio

    dir_start = cluster_size
    entry_size = 64
    posicion_entrada = dir_start + (entrada_libre * entry_size)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")  # Ej: "20260517143000"

    # Construir la entrada del directorio (64 bytes)
    entrada = bytearray(64)

    entrada[0] = ord('-')  # Tipo de archivo: '-' para archivos ocupados

    nombre_bytes = nombre_destino.encode('ascii')
    entrada[1:1+len(nombre_bytes)] = nombre_bytes
    # Rellenar el resto del nombre con ceros
    for i in range(1 + len(nombre_bytes), 16):
        entrada[i] = 0
    
    entrada[16:20] = struct.pack('<I', tamaño_archivo)
    entrada[20:24] = struct.pack('<I', primer_cluster)
    timestamp_bytes = timestamp.encode('ascii')
    entrada[30:30+len(timestamp_bytes)] = timestamp_bytes

    entrada[50:50+len(timestamp_bytes)] = timestamp_bytes

    data[posicion_entrada:posicion_entrada + 64] = entrada
    print(f"Guardando cambios en {img_path}...")

    try:
        with open(img_path, 'wb') as f:
            f.write(data)
        
        print(f"¡Archivo copiado exitosamente!")
        print(f"Nombre: {nombre_destino}")
        print(f"Tamaño: {tamaño_archivo} bytes")
        print(f"Cluster inicial: {primer_cluster}")
        print(f"Entrada del directorio: #{entrada_libre}")
        print(f"Fecha: {timestamp}")
        
        return True
        
    except Exception as e:
        print(f"Error al guardar el archivo .img: {e}")
        return False
    
def main():
    # Ejemplo de uso:
    # python paste.py fiunamfs.img ruta/al/archivo/local.txt nombre_destino

    img_path = sys.argv[1] # fiunamfs.img
    archivo_local = sys.argv[2] # ruta al archivo local que queremos copiar
    nombre_destino = sys.argv[3] if len(sys.argv) > 3 else None 

    print("=" * 60)
    print("COPIA DE ARCHIVO A FIUNAMFS")
    print("=" * 60)
    print()
    
    success = copy(img_path, archivo_local, nombre_destino)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":  
    main()


    

    



    

