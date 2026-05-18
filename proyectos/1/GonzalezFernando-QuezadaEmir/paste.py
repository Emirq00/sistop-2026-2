from pathlib import Path
import sys
import struct
from datetime import datetime
from math import ceil
from functions import paste
    
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
    
    success = paste(img_path, archivo_local, nombre_destino)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":  
    main()


    

    



    

