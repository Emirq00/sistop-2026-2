#!/usr/bin/env python3
"""
minishell.py
Intérprete de comandos mínimo para Unix/Linux.

Características:
- Muestra un prompt y lee comandos.
- Parsea argumentos con shlex.split().
- Crea procesos con os.fork().
- Ejecuta programas con os.execvp().
- Recolecta hijos terminados con SIGCHLD + os.waitpid(..., os.WNOHANG).
- Ignora SIGINT (Ctrl+C) en el shell padre.
- Restaura el comportamiento por defecto de SIGINT en los hijos.
- Implementa el comando interno 'exit'.

Restricciones:
- No implementa pipes, redirecciones, variables de entorno ni jobs.
- Diseñado para Unix/Linux.
"""

import errno
import os
import shlex
import signal
import sys

# Conjunto global para registrar PIDs de hijos que ya terminaron.
# El manejador SIGCHLD los va agregando aquí.
terminated_children = set()


def sigchld_handler(signum, frame):
    """
    Manejador de SIGCHLD.

    Recolecta todos los hijos que ya terminaron sin bloquear, usando:
        os.waitpid(-1, os.WNOHANG)

    Se repite en bucle porque pueden haber terminado varios hijos antes de que
    el proceso padre atienda la señal.
    """
    try:
        while True:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                # No hay hijos terminados pendientes por recolectar.
                break

            # Guardamos el PID como terminado para que el bucle principal lo note.
            terminated_children.add(pid)

    except ChildProcessError:
        # No existen procesos hijos.
        pass
    except OSError:
        # Evita que un error raro en waitpid rompa el shell.
        pass


def install_signal_handlers():
    """
    Instala los manejadores de señales del shell.

    - SIGCHLD: recolecta hijos terminados.
    - SIGINT : se ignora en el shell padre para que Ctrl+C no lo mate.
    """
    signal.signal(signal.SIGCHLD, sigchld_handler)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def parse_command(line):
    """
    Convierte una línea de texto en lista de argumentos.

    Usa shlex.split para respetar comillas, por ejemplo:
        echo "Hola mundo"

    Regresa:
    - lista de tokens si todo salió bien
    - None si hubo error de sintaxis
    """
    try:
        return shlex.split(line)
    except ValueError as e:
        print(f"Error de sintaxis al parsear el comando: {e}", file=sys.stderr)
        return None


def wait_for_child(pid):
    """
    Espera a que un hijo específico termine, pero delegando la recolección real
    al manejador SIGCHLD.

    En vez de hacer waitpid(pid, 0) directamente, aquí esperamos hasta que
    el manejador SIGCHLD haya marcado ese PID como terminado.
    """
    while pid not in terminated_children:
        try:
            signal.pause()
        except InterruptedError:
            # Si pause() es interrumpido por otra señal, seguimos esperando.
            continue

    terminated_children.discard(pid)


def execute_command(argv):
    """
    Ejecuta un comando externo:
    - fork()
    - en el hijo: restaura SIGINT por defecto y llama execvp()
    - en el padre: espera a que SIGCHLD recolecte al hijo

    Devuelve:
    - True si el shell debe continuar
    - False si debe salir
    """
    if not argv:
        return True

    # Comando interno: exit
    if argv[0] == "exit":
        return False

    try:
        pid = os.fork()
    except OSError as e:
        print(f"Error: no se pudo crear el proceso hijo: {e}", file=sys.stderr)
        return True

    if pid == 0:
        # ===== PROCESO HIJO =====
        try:
            # En el hijo sí queremos el comportamiento normal de Ctrl+C.
            signal.signal(signal.SIGINT, signal.SIG_DFL)

            # Reemplaza la imagen del proceso con el programa solicitado.
            os.execvp(argv[0], argv)

        except FileNotFoundError:
            print(f"{argv[0]}: comando no encontrado", file=sys.stderr)
        except PermissionError:
            print(f"{argv[0]}: permiso denegado", file=sys.stderr)
        except OSError as e:
            print(f"Error al ejecutar '{argv[0]}': {e}", file=sys.stderr)

        # Si execvp falla, el hijo debe terminar explícitamente.
        os._exit(127)

    else:
        # ===== PROCESO PADRE =====
        wait_for_child(pid)
        return True


def main():
    install_signal_handlers()

    while True:
        try:
            line = input("minishell> ")
        except EOFError:
            # Ctrl+D: salir limpiamente
            print()
            break
        except KeyboardInterrupt:
            # Normalmente no debería entrar aquí porque SIGINT está ignorada,
            # pero lo manejamos por robustez.
            print()
            continue

        line = line.strip()
        if not line:
            continue

        argv = parse_command(line)
        if argv is None:
            continue

        should_continue = execute_command(argv)
        if not should_continue:
            break

    print("Saliendo de minishell.")


if __name__ == "__main__":
    main()