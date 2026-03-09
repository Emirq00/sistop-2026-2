import os
import sys
import signal

def handler_sigint(sig, frame):
    """Manejador para que el shell no muera con Ctrl+C."""
    print("\n[Mini-Shell] Usa 'exit' para salir.")
    # No hace nada más, solo imprime y permite que el ciclo continúe

def mini_shell():
    # Registrar el manejador de señales (Ctrl+C)
    signal.signal(signal.SIGINT, handler_sigint)

    print("--- Bienvenido al Mini-Shell Sistop 2026-2 ---")
    
    while True:
        try:
            # 1. Mostrar el Prompt
            prompt = f"{os.getcwd()} $ "
            entrada = input(prompt).strip()

            # Si el usuario no escribe nada, saltar
            if not entrada:
                continue

            # 2. Comando para salir
            if entrada.lower() in ['exit', 'quit']:
                print("Saliendo del shell...")
                break

            # 3. Parsear la entrada (separar comando de argumentos)
            args = entrada.split()
            comando = args[0]

            # 4. Bifurcar el proceso (Fork)
            pid = os.fork()

            if pid == 0:
                # --- PROCESO HIJO ---
                try:
                    # Intentamos ejecutar el comando
                    # execvp busca el comando en el PATH automáticamente
                    os.execvp(comando, args)
                except FileNotFoundError:
                    print(f"Error: El comando '{comando}' no fue encontrado.")
                    sys.exit(1)
                except Exception as e:
                    print(f"Error al ejecutar: {e}")
                    sys.exit(1)
            else:
                # --- PROCESO PADRE ---
                # Esperamos a que el hijo termine para no dejarlo "Zombie"
                # os.wait() devuelve (pid, status)
                _, status = os.waitpid(pid, 0)
                
                # Opcional: ver si el hijo terminó con error
                if os.WIFEXITED(status) and os.WEXITSTATUS(status) != 0:
                    pass # El hijo ya imprimió su error

        except EOFError:
            # Manejar Ctrl+D para salir limpiamente
            print("\nSaliendo...")
            break
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    mini_shell()
