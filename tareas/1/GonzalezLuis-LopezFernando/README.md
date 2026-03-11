# Tarea 1 Minishell — Intérprete de comandos mínimo

## Autores
Gonzalez Falcón Luis Adrián
López Morales Fernando Samuel

---
# Instrucciones de compilación / ejecución

## Compilación

Para compilar el programa es necesario contar con un compilador de C como **gcc**.

Ejecutar el siguiente comando en la terminal dentro del directorio donde se encuentra el archivo fuente:
```shell
gcc minishell.c -o minishell
```

Este comando generará un ejecutable llamado `minishell`.

---
## Ejecución

Una vez compilado el programa, se puede ejecutar con:
```shell
./minishell
```


Al ejecutarlo aparecerá el prompt del intérprete:
```shell
minishell>
```


Desde ahí es posible introducir comandos del sistema operativo.
```shell
minishell> ls  
minishell> pwd  
minishell> sleep 5  
minishell> exit
```

## Salir del minishell
El comando `exit` finaliza la ejecución del minishell.

# Ejemplo de ejecución
![](Anexos/Ejemplo%20de%20ejecucion.png)

# Breve explicación del diseño

El minishell fue diseñado siguiendo el modelo básico de funcionamiento de un intérprete de comandos en sistemas tipo Unix. El programa se estructura alrededor de un ciclo principal que se encarga de leer comandos del usuario, procesarlos y ejecutarlos mediante la creación de procesos hijos.

## Ciclo principal del shell

El funcionamiento general se basa en un ciclo infinito que realiza los siguientes pasos:

1. Mostrar el **prompt** (`minishell>`) para indicar que el shell está listo para recibir comandos.
2. Leer la línea introducida por el usuario utilizando `fgets`.
3. Separar el comando y sus argumentos utilizando `strtok`, generando un arreglo de cadenas compatible con `execvp`.
4. Verificar si el comando corresponde a `exit`, en cuyo caso se termina la ejecución del shell.
5. Crear un proceso hijo mediante `fork`.
6. Ejecutar el programa solicitado en el proceso hijo utilizando `execvp`.
7. El proceso padre espera la finalización del hijo mediante `waitpid`.

## Manejo de señales

El diseño también incluye el manejo de señales para controlar correctamente el comportamiento del shell y evitar problemas comunes como procesos zombie.

Se instala un **handler de señales** mediante `sigaction` para manejar principalmente:

- **SIGCHLD**: se utiliza para recolectar procesos hijos terminados mediante `waitpid(-1, &status, WNOHANG)`. Esto evita la acumulación de procesos zombie.
- **SIGINT (Ctrl+C)**: el shell ignora esta señal para evitar que el intérprete termine cuando el usuario presiona Ctrl+C. Sin embargo, los procesos hijos restauran el comportamiento por defecto de la señal para que puedan ser interrumpidos normalmente.

## Separación entre proceso padre e hijo

El diseño diferencia claramente las responsabilidades de cada proceso:

- **Proceso padre (shell)**  
  - Controla el ciclo principal del programa.
  - Maneja las señales.
  - Espera la terminación de los procesos hijos.

- **Proceso hijo**  
  - Ejecuta el comando solicitado mediante `execvp`.
  - Restablece el comportamiento por defecto de `SIGINT`.

Esta separación permite que el shell continúe funcionando incluso cuando se ejecutan programas externos o cuando estos son interrumpidos por el usuario.

# Dificultades encontradas y cómo se resolvieron

Durante el desarrollo del minishell surgieron diversas dificultades relacionadas principalmente con el manejo de procesos y señales en sistemas Unix.

## 1. Manejo incorrecto de procesos hijos

Una de las primeras dificultades fue entender cómo debía el proceso padre recolectar la terminación de los procesos hijos. Inicialmente se utilizó `wait(NULL)` directamente en el flujo del programa, lo cual bloqueaba al shell hasta que el proceso hijo terminara.

Para resolver esto se investigó el uso de `waitpid()` junto con la opción `WNOHANG`, que permite consultar si algún hijo ha terminado **sin bloquear la ejecución del proceso padre**. Esto se implementó dentro de un manejador de la señal `SIGCHLD`, utilizando el siguiente patrón:

```C
while ((pid = waitpid(-1, &status, WNOHANG)) > 0)
```


El uso del ciclo `while` permite recolectar **todos los procesos hijos que hayan terminado**, evitando así la acumulación de procesos zombie.

---

## 2. Comportamiento de la señal SIGINT

Otra dificultad fue implementar correctamente el comportamiento solicitado para `SIGINT` (generada al presionar `Ctrl+C`).  
El requerimiento era que el **shell padre ignorara la señal**, mientras que los **procesos hijos debían responder a ella normalmente**.

Inicialmente, al ignorar la señal en el shell, los procesos hijos heredaban este comportamiento y tampoco podían ser interrumpidos.

La solución fue que, dentro del proceso hijo, se restaurara el comportamiento por defecto de la señal mediante:


```C
sa.sa_handler = SIG_DFL;  
sigaction(SIGINT, &sa, NULL);
```

De esta manera el shell continúa ejecutándose, pero los programas lanzados por él sí pueden ser terminados con `Ctrl+C`.

---

## 3. Manejo de entradas vacías

Durante las pruebas se detectó que al presionar **Enter sin escribir ningún comando**, el programa podía intentar ejecutar un comando inexistente.

Esto se debía a que `strtok()` regresaba `NULL` cuando no encontraba tokens en la cadena de entrada.

Para evitar este problema se agregó la validación:

```C
if (parametros[0] == NULL) continue;
```


lo que permite que el shell simplemente vuelva a mostrar el prompt.


## 4. Eliminación del salto de línea en la entrada

La función `fgets()` incluye el carácter de nueva línea (`\n`) al final de la cadena leída. Esto provocaba problemas al comparar comandos como `exit`.

La solución fue eliminar el salto de línea con:


```C
input[strcspn(input, "\n")] = '\0';
```


Esto permite trabajar con la cadena de entrada sin caracteres adicionales.

## 5. Terminación del proceso hijo cuando falla execvp

Se detectó que si `execvp()` fallaba, el proceso hijo continuaba ejecutando el ciclo del shell, lo que podía generar múltiples instancias del intérprete.

Para evitar este comportamiento se añadió la terminación explícita del proceso hijo en caso de error:

```C
perror("execvp");  
_exit(1);
```

Esto asegura que el proceso hijo termine inmediatamente si no puede ejecutar el programa solicitado.