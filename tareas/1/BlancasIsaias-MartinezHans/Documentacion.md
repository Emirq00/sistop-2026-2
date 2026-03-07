# Tarea 1: Implementación de un intérprete de comandos mínimo (minishell)
**Fecha:** 07 de Marzo 2026 
**Autores:** Isaías Blancas Díaz y Martínez Sánchez Hans  
**Materia:** Sistemas Operativos  
**Grupo:** 07 
 

## 1. Explicación del diseño
El minishell está diseñado como un ciclo infinito de lectura y ejecución (REPL). Su arquitectura se basa en tres bases de sistemas Unix:
* **Creación de procesos:** Se utiliza la llamada al sistema `os.fork()` para clonar el shell. El proceso hijo es el encargado de ejecutar la tarea, mientras el padre mantiene el control de la terminal.
* **Sustitución de imagen:** En el hijo, se usa `os.execvp()` para reemplazar el código del shell por el del programa solicitado (ej. `ls`, `ps`), buscándolo automáticamente en las rutas del sistema.
* **Manejo de señales:** El shell es asíncrono. No se queda bloqueado esperando al hijo, sino que utiliza un manejador para la señal `SIGCHLD` que recoge a los hijos terminados mediante `os.waitpid(-1, os.WNOHANG)`, evitando así que se conviertan en procesos zombie.

## 2. Instrucciones de compilación/ejecución
Al estar desarrollado en Python 3, el programa **no requiere compilación**, pero es obligatorio ejecutarlo en un entorno **Linux o Unix** debido a que utiliza llamadas al sistema específicas de estos núcleos.

**Para ejecutar el programa:**
1. Abre una terminal de Linux.
2. Navega hasta la carpeta donde se encuentra el archivo `Minishell.py`.
3. Ejecuta el comando:

" ```bash "
" python3 Minishell.py "


## 3. Ejemplo de ejecución

Minishell> pwd
Minishell> /home/saiblancs
ls -l
Minishell> total 8
-rw-r--r-- 1 saiblancs saiblancs 2848 Mar  7 03:19 'import os #para llamar al sistema (fork,.py'
-rwxr-xr-x 1 saiblancs saiblancs  913 Mar  7 03:19  README-cloudshell.txt
echo Aqui Isaias probando el minishell
Minishell> Aqui Isaias probando el minishell


## 4. Dificultades encontradas

1. **Manejo de Ctrl+C (SIGINT):** Al presionar `Ctrl+C`, tanto el proceso hijo como el shell padre terminaban su ejecución simultáneamente. 
    **Solución:** Se configuró el proceso padre para ignorar la señal mediante `signal.SIG_IGN`. Para evitar que los procesos hijos también la ignoraran, se restauró el comportamiento predeterminado con `signal.SIG_DFL` justo después del `fork()`, permitiendo interrumpir comandos externos sin cerrar el shell.

2. **Procesos Zombie:** Se observó que los procesos hijos que terminaban su ejecución permanecían en la tabla de procesos del sistema con el estado `<defunct>`. 
    **Solución:** Se implementó un manejador de señales para `SIGCHLD` que utiliza `os.waitpid(-1, os.WNOHANG)`. Esto permite que el padre recoja el estado de los hijos de manera asíncrona y no bloqueante, liberando los recursos del sistema de inmediato.