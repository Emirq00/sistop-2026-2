#!/usr/bin/env python3
"""
Minishell - Intérprete de comandos mínimo
Autor: Fernando Ortega
Fecha: 2026-03-10

Este programa implementa un shell básico que permite ejecutar programas
del sistema, manejando la creación de procesos con fork(), ejecución con
exec() y recolección de procesos hijos con señales (SIGCHLD).
"""

import os
import signal
import sys
import shlex

# Bandera global para indicar si hay un hijo que terminó
# Se usa una bandera en lugar de procesar directamente en el manejador
# porque los manejadores de señales deben ser lo más simples posible
hijo_terminado = False


def manejador_sigchld(signum, frame):
    """
    Manejador de la señal SIGCHLD.
    
    Se ejecuta cuando un proceso hijo termina. Utiliza waitpid() con WNOHANG
    para recolectar los procesos hijos de forma no bloqueante, lo que permite
    recoger múltiples hijos que hayan terminado simultáneamente.
    
    Args:
        signum: Número de la señal recibida (SIGCHLD)
        frame: Marco de pila actual (no utilizado)
    """
    global hijo_terminado
    try:
        # Intentamos recolectar todos los hijos que hayan terminado
        # WNOHANG hace que waitpid() no se bloquee si no hay hijos
        while True:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                # No hay más hijos terminados por recolectar
                break
            # Marcamos que al menos un hijo terminó
            hijo_terminado = True
    except ChildProcessError:
        # No hay procesos hijos (ya fueron recolectados o no existen)
        pass


def manejador_sigint(signum, frame):
    """
    Manejador de la señal SIGINT (Ctrl+C).
    
    El shell padre ignora esta señal para que no termine cuando el usuario
    presiona Ctrl+C. Los procesos hijos restaurarán el comportamiento
    predeterminado (terminar).
    
    Args:
        signum: Número de la señal recibida (SIGINT)
        frame: Marco de pila actual (no utilizado)
    """
    # Simplemente imprimimos una nueva línea para mantener el prompt limpio
    print()


def configurar_senales():
    """
    Configura los manejadores de señales para el shell.
    
    - SIGCHLD: Para recolectar procesos hijos que terminan
    - SIGINT: Para ignorar Ctrl+C en el shell padre
    """
    # Instalamos el manejador para SIGCHLD
    # Esto permite recolectar hijos de forma asíncrona
    signal.signal(signal.SIGCHLD, manejador_sigchld)
    
    # Instalamos el manejador para SIGINT
    # El shell no debe terminar con Ctrl+C
    signal.signal(signal.SIGINT, manejador_sigint)


def parsear_comando(linea):
    """
    Separa la línea de comando en programa y argumentos.
    
    Utiliza shlex.split() que maneja correctamente las comillas y
    caracteres de escape, similar a como lo hace un shell real.
    
    Args:
        linea: Cadena con el comando ingresado por el usuario
        
    Returns:
        Lista de argumentos donde el primero es el programa a ejecutar,
        o None si la línea está vacía o hay un error de sintaxis
    """
    try:
        # shlex.split maneja comillas y escapes correctamente
        # Por ejemplo: echo "Hola mundo" -> ['echo', 'Hola mundo']
        args = shlex.split(linea)
        return args if args else None
    except ValueError as e:
        # Error de sintaxis (por ejemplo, comillas sin cerrar)
        print(f"minishell: error de sintaxis: {e}")
        return None


def es_comando_interno(args):
    """
    Verifica si el comando es interno del shell.
    
    Los comandos internos son aquellos que el shell maneja directamente
    sin crear un proceso hijo.
    
    Args:
        args: Lista de argumentos del comando
        
    Returns:
        True si es un comando interno, False en caso contrario
    """
    comandos_internos = ['exit', 'salir', 'quit']
    return args[0].lower() in comandos_internos


def ejecutar_comando_interno(args):
    """
    Ejecuta un comando interno del shell.
    
    Args:
        args: Lista de argumentos del comando
        
    Returns:
        True si el shell debe continuar, False si debe terminar
    """
    comando = args[0].lower()
    
    if comando in ['exit', 'salir', 'quit']:
        print("¡Hasta luego!")
        return False
    
    return True


def ejecutar_comando_externo(args):
    """
    Ejecuta un comando externo creando un proceso hijo.
    
    Proceso:
    1. Se crea un proceso hijo con fork()
    2. El hijo reemplaza su imagen con exec() para ejecutar el programa
    3. El padre espera (de forma bloqueante) a que el hijo termine
    
    El manejador de SIGCHLD se encarga de la recolección asíncrona del hijo.
    
    Args:
        args: Lista donde args[0] es el programa y el resto son argumentos
    """
    global hijo_terminado
    
    try:
        # Creamos el proceso hijo
        pid = os.fork()
        
        if pid == 0:
            # ===== PROCESO HIJO =====
            
            # Restauramos el comportamiento predeterminado de SIGINT
            # para que el hijo pueda ser interrumpido con Ctrl+C
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            
            try:
                # execvp busca el programa en PATH y lo ejecuta
                # Reemplaza completamente la imagen del proceso
                os.execvp(args[0], args)
            except FileNotFoundError:
                # El programa no se encontró en PATH
                print(f"minishell: {args[0]}: comando no encontrado")
                sys.exit(127)  # Código de error estándar para "comando no encontrado"
            except PermissionError:
                # No se tiene permiso para ejecutar el programa
                print(f"minishell: {args[0]}: permiso denegado")
                sys.exit(126)  # Código de error para "permiso denegado"
            except Exception as e:
                print(f"minishell: error al ejecutar '{args[0]}': {e}")
                sys.exit(1)
        
        elif pid > 0:
            # ===== PROCESO PADRE =====
            
            # Reiniciamos la bandera antes de esperar
            hijo_terminado = False
            
            # Esperamos a que el hijo termine
            # Aunque tenemos SIGCHLD, hacemos una espera explícita para
            # asegurar que no continuemos hasta que el hijo termine
            try:
                # waitpid bloqueante para esperar específicamente a este hijo
                os.waitpid(pid, 0)
            except ChildProcessError:
                # El hijo ya fue recolectado por el manejador de SIGCHLD
                pass
            except InterruptedError:
                # La espera fue interrumpida por una señal (probablemente SIGCHLD)
                # Intentamos recolectar el hijo de nuevo
                try:
                    os.waitpid(pid, 0)
                except ChildProcessError:
                    pass
        
        else:
            # fork() falló (pid < 0)
            print("minishell: error: no se pudo crear el proceso hijo")
            
    except OSError as e:
        print(f"minishell: error del sistema: {e}")


def mostrar_prompt():
    """
    Muestra el prompt del shell y espera entrada del usuario.
    
    Returns:
        La línea ingresada por el usuario, o None si hay EOF (Ctrl+D)
    """
    try:
        # Usamos sys.stdout.write y flush para asegurar que el prompt
        # se muestre inmediatamente antes de leer la entrada
        sys.stdout.write("minishell> ")
        sys.stdout.flush()
        linea = sys.stdin.readline()
        
        # Si readline() retorna cadena vacía, es EOF (Ctrl+D)
        if not linea:
            return None
        
        # Removemos el salto de línea final
        return linea.strip()
        
    except EOFError:
        return None
    except KeyboardInterrupt:
        # Ctrl+C durante la lectura
        print()
        return ""


def bucle_principal():
    """
    Bucle principal del shell.
    
    Lee comandos del usuario, los parsea y los ejecuta hasta que
    el usuario ingrese 'exit' o presione Ctrl+D.
    """
    while True:
        # Mostramos el prompt y leemos el comando
        linea = mostrar_prompt()
        
        # EOF (Ctrl+D) - terminamos el shell
        if linea is None:
            print("\n¡Hasta luego!")
            break
        
        # Línea vacía - continuamos
        if not linea:
            continue
        
        # Parseamos el comando
        args = parsear_comando(linea)
        
        # Si el parseo falló o la línea estaba vacía, continuamos
        if not args:
            continue
        
        # Verificamos si es un comando interno
        if es_comando_interno(args):
            if not ejecutar_comando_interno(args):
                break
        else:
            # Ejecutamos el comando externo
            ejecutar_comando_externo(args)


def main():
    """
    Función principal del programa.
    
    Configura las señales e inicia el bucle principal del shell.
    """
    # Verificamos que estemos en un sistema Unix/Linux
    if os.name != 'posix':
        print("Error: Este programa solo funciona en sistemas Unix/Linux")
        print("(Requiere fork(), exec() y señales POSIX)")
        sys.exit(1)
    
    print("=" * 50)
    print("  Minishell - Intérprete de comandos mínimo")
    print("  Escribe 'exit' para salir")
    print("=" * 50)
    
    # Configuramos los manejadores de señales
    configurar_senales()
    
    # Iniciamos el bucle principal
    bucle_principal()
    
    # Salimos limpiamente
    sys.exit(0)


if __name__ == "__main__":
    main()
