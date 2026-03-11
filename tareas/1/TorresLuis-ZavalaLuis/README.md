# Minishell en Python

**Autor**  
* Luis Torres Lozano
* Luis Arturo Zavala Magaña

En esta tarea se implementó un intérprete de comandos básico en Python. El programa es compatible con sistemas Unix/Linux y permite ejecutar comandos simples del sistema mediante creación de procesos y manejo de señales.

## Instrucciones de compilación y ejecución

Como el programa está escrito en Python, no requiere compilación previa.  
Solo es necesario verificar que Python 3 esté instalado en el sistema y ejecutar el archivo con:

```bash
python3 minishell.py

Si se trabajó desde Windows con WSL, primero se debe entrar a la carpeta del proyecto, por ejemplo:

```bash
cd "/mnt/c/Users/luist/OneDrive/Escritorio/Sistemas Operativos Prog"
python3 minishell.py
```

## Explicación del diseño
En este programa:

Se utiliza os.fork() para crear un proceso hijo cada vez que el usuario ingresa un comando.

En el proceso hijo se usa os.execvp() para ejecutar el comando solicitado con sus argumentos.

Para separar correctamente el comando y sus argumentos se usa shlex.split(), lo que permite manejar entradas con comillas como echo "Hola mundo".

Se instala un manejador para la señal SIGCHLD, en donde se utiliza os.waitpid(-1, os.WNOHANG) para recolectar procesos hijos terminados sin bloquear al shell.

El proceso padre ignora la señal SIGINT de Ctrl+C para que el minishell no termine accidentalmente.

En cambio, el proceso hijo restablece el comportamiento normal de SIGINT, de modo que sí pueda interrumpirse un comando en ejecución.

Además, se implementó el comando interno exit para terminar el shell de manera limpia.

## Ejemplo de ejecución
```bash
minishell> ls
Documentos  Descargas  minishell.py
minishell> echo "Hola mundo"
Hola mundo
minishell> sleep 5
minishell> exit
Saliendo de minishell.
```
## Dificultades encontradas
La principal dificultad fue que el programa no podía ejecutarse directamente en Windows, ya que funciones como os.fork() y la señal SIGCHLD no están disponibles de la misma manera fuera de Unix/Linux. Para resolver esto, se utilizó WSL con Ubuntu, lo que permitió contar con un entorno Linux dentro de Windows y ejecutar correctamente el programa.

Otra dificultad fue entender bien cómo manejar la terminación de los procesos hijo sin bloquear el shell. Al principio podía ser confuso cómo combinar la espera del hijo con el manejo asíncrono de SIGCHLD, pero esto se resolvió usando os.waitpid(-1, os.WNOHANG) dentro del manejador de la señal.

También surgió el problema de manejar Ctrl+C correctamente. Era necesario que el shell no se cerrara al presionar esa combinación, pero que un comando hijo como sleep 10 sí pudiera interrumpirse. Esto se resolvió ignorando SIGINT en el proceso padre y restaurando su comportamiento por defecto en el proceso hijo.