# Minishell - Intérprete de Comandos Mínimo

**Autor:** Fernando Ortega  
**Fecha:** 2026-03-10  
**Materia:** Sistemas Operativos

## Descripción

Implementación de un intérprete de comandos básico (shell) que permite ejecutar programas del sistema, manejando correctamente:
- Creación de procesos mediante `fork()`
- Ejecución de programas con `exec()`
- Recolección de procesos hijos con señales (`SIGCHLD`)
- Manejo de interrupción (`SIGINT` / Ctrl+C)

## Instrucciones de Ejecución

### Requisitos
- Python 3.6 o superior
- Sistema operativo Unix/Linux (el programa utiliza llamadas al sistema POSIX)

### Ejecución

```bash
# Dar permisos de ejecución (opcional)
chmod +x minishell.py

# Ejecutar con Python
python3 minishell.py

# O directamente si tiene permisos de ejecución
./minishell.py
```

## Diseño del Programa

### Arquitectura General

El programa sigue un diseño modular con las siguientes componentes principales:

```
┌─────────────────────────────────────────────────────────┐
│                    BUCLE PRINCIPAL                       │
│  ┌─────────┐    ┌─────────┐    ┌──────────────────────┐ │
│  │ Mostrar │───▶│ Parsear │───▶│ Ejecutar comando     │ │
│  │ Prompt  │    │ Comando │    │ (interno o externo)  │ │
│  └─────────┘    └─────────┘    └──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              MANEJADORES DE SEÑALES                      │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │ SIGCHLD:        │    │ SIGINT:                     │ │
│  │ Recolecta hijos │    │ Ignorado en padre           │ │
│  │ con waitpid()   │    │ (hijos usan default)        │ │
│  └─────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Ejecución de un Comando

1. **Lectura**: El shell muestra el prompt y lee la entrada del usuario
2. **Parseo**: Se utiliza `shlex.split()` para separar el comando en programa y argumentos, respetando comillas
3. **Clasificación**: Se determina si es un comando interno (`exit`) o externo
4. **Ejecución**:
   - **Interno**: Se ejecuta directamente en el proceso padre
   - **Externo**: Se crea un proceso hijo con `fork()`:
     - El hijo ejecuta el programa con `execvp()`
     - El padre espera con `waitpid()`

### Manejo de Señales

#### SIGCHLD
- Se instala un manejador que llama a `waitpid(-1, WNOHANG)` en un bucle
- `WNOHANG` evita que se bloquee si no hay hijos terminados
- El bucle recolecta múltiples hijos que podrían haber terminado simultáneamente

#### SIGINT (Ctrl+C)
- El proceso padre ignora esta señal (imprime una nueva línea para limpiar el prompt)
- Los procesos hijos restauran el comportamiento predeterminado antes de ejecutar `exec()`
- Esto permite interrumpir comandos en ejecución sin matar el shell

## Ejemplo de Ejecución

```
$ python3 minishell.py
==================================================
  Minishell - Intérprete de comandos mínimo
  Escribe 'exit' para salir
==================================================
minishell> ls -la
total 16
drwxr-xr-x 2 user user 4096 mar 10 10:00 .
drwxr-xr-x 3 user user 4096 mar 10 09:55 ..
-rwxr-xr-x 1 user user 5432 mar 10 10:00 minishell.py
-rw-r--r-- 1 user user 2048 mar 10 10:05 README.md

minishell> echo "Hola mundo desde minishell"
Hola mundo desde minishell

minishell> ps aux | head -5
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 168936 11520 ?        Ss   09:00   0:01 /sbin/init
root         2  0.0  0.0      0     0 ?        S    09:00   0:00 [kthreadd]
...

minishell> whoami
user

minishell> pwd
/home/user/tareas/1

minishell> comando_inexistente
minishell: comando_inexistente: comando no encontrado

minishell> exit
¡Hasta luego!
```

### Prueba con Ctrl+C

```
minishell> sleep 10
^C                          # <-- El usuario presiona Ctrl+C
                            # El comando sleep se interrumpe
minishell>                  # El shell sigue funcionando

minishell> ^C               # Ctrl+C sin comando
                            # El shell no termina, solo imprime nueva línea
minishell> exit
¡Hasta luego!
```

## Dificultades Encontradas y Soluciones

### 1. Señal SIGCHLD interrumpiendo waitpid()

**Problema:** Cuando el proceso hijo terminaba, `waitpid()` en el padre a veces era interrumpido por la señal `SIGCHLD` antes de que pudiera recolectar el hijo, causando un error `InterruptedError`.

**Solución:** Se implementó un manejo de excepciones que captura `InterruptedError` y reintenta la recolección del hijo:
```python
try:
    os.waitpid(pid, 0)
except InterruptedError:
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass  # Ya fue recolectado por el manejador
```

### 2. Manejo correcto de Ctrl+C

**Problema:** Si el proceso hijo hereda el manejador de `SIGINT` del padre (que ignora la señal), los comandos no pueden ser interrumpidos.

**Solución:** En el proceso hijo, inmediatamente después del `fork()`, se restaura el comportamiento predeterminado de `SIGINT`:
```python
if pid == 0:  # Proceso hijo
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.execvp(...)
```

### 3. Parseo de comandos con comillas

**Problema:** Implementar un parser manual para manejar comillas, escapes y espacios es propenso a errores.

**Solución:** Se utiliza el módulo `shlex` de Python que implementa un tokenizador compatible con POSIX:
```python
# "echo 'Hola mundo'" -> ['echo', 'Hola mundo']
args = shlex.split(linea)
```

### 4. Condición de carrera con procesos zombie

**Problema:** Si el manejador de `SIGCHLD` recolecta el hijo antes de que el padre llame a `waitpid()`, este último falla con `ChildProcessError`.

**Solución:** Se captura la excepción `ChildProcessError` y se trata como un caso válido (el hijo ya fue recolectado):
```python
try:
    os.waitpid(pid, 0)
except ChildProcessError:
    pass  # El hijo ya fue recolectado por el manejador SIGCHLD
```

## Estructura del Código

```
minishell.py
├── manejador_sigchld()     # Recolecta procesos hijos terminados
├── manejador_sigint()      # Ignora Ctrl+C en el shell
├── configurar_senales()    # Instala los manejadores
├── parsear_comando()       # Tokeniza la línea de entrada
├── es_comando_interno()    # Verifica si es exit/salir/quit
├── ejecutar_comando_interno()  # Ejecuta comandos internos
├── ejecutar_comando_externo()  # fork() + exec()
├── mostrar_prompt()        # Muestra prompt y lee entrada
├── bucle_principal()       # Loop principal del shell
└── main()                  # Punto de entrada
```

## Limitaciones

- No soporta tuberías (`|`) ni redirecciones (`>`, `<`, `>>`)
- No soporta variables de entorno ni expansión de variables
- No soporta ejecución en segundo plano (`&`)
- No soporta historial de comandos ni autocompletado
- Requiere un sistema Unix/Linux (no funciona en Windows nativo)

## Referencias

- Manual de Python: [os — Miscellaneous operating system interfaces](https://docs.python.org/3/library/os.html)
- Manual de Python: [signal — Set handlers for asynchronous events](https://docs.python.org/3/library/signal.html)
- Manual de Linux: `man 2 fork`, `man 3 exec`, `man 2 waitpid`, `man 7 signal`
