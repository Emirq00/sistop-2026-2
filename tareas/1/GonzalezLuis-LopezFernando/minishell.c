#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>

#define MAX_INPUT 500
#define MAX_TOKENS 50
#define COMANDO_SALIDA "exit"
void handler(int signo);

void instalar_handlers() {
    struct sigaction sa;

    sa.sa_handler = handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;

    sigaction(SIGCHLD, &sa, NULL);

    /* ignorar SIGINT */
    sigaction(SIGINT, &sa, NULL);
}
void handler(int signo){
    // Caso de SIGCHLD
    switch(signo){
        case SIGCHLD:
            int status;
            pid_t pid;
            while ((pid = waitpid(-1, &status, WNOHANG)) > 0);
            break;
        case SIGINT:
            //no hace nada xd
            break;
    }
}

//Shell (todo el funcionamiento)
void minishell(){
    char input[MAX_INPUT];
    char* parametros[MAX_TOKENS];

    // Ciclo donde vive la terminal
    while (1){
        // (1) Imprime el prompt
        printf("minishell> ");
        fflush(stdout);

        // (2) leer linea usuario
        //Se recibe el texto introducido por el usuairo:
        fgets(input, sizeof(input), stdin);
        input[strcspn(input, "\n")] = '\0';

        // Tokenizar los comandos
        int i_parametros = 0;
        char* token = strtok(input, " ");
        
        while (token != NULL){
            parametros[i_parametros++] = token;
            token = strtok(NULL, " ");
        }
        // Es importante el NULL, porque execvp espera un array con el último elemento en NULL
        parametros[i_parametros] = NULL;

        //Evita que el codigo muera cuando se entrege una cadena vacia ("enter")
        if (parametros[0] == NULL) continue;

        int tam_comando = strlen(parametros[0]);
        char comando[tam_comando+1];
        strcpy(comando, parametros[0]);

        if(strcmp(comando, COMANDO_SALIDA)==0){
            printf("Regresa pronto a minishell!\nAdios :)\n");
            break;
        } else {
            // CREACIÓN DEL FORK
            pid_t nvo_pid = fork();
            pid_t pid = getpid();
        

            if (nvo_pid < 0){ // fork sin exito
                printf("Hubo un error en el fork\n");
                printf("Terminando sin exito\n");
            }else if (nvo_pid == 0){ // pid del hijo
                // Sobreescribe la señal de SIG_IGN del padre de ignorarla
                struct sigaction sa;
                //SIG_DFL: es la acción definida de la señal
                sa.sa_handler = SIG_DFL;
                sigemptyset(&sa.sa_mask);
                sa.sa_flags = SA_RESTART;
                sigaction(SIGINT, &sa, NULL);
                execvp(comando, parametros);
                perror("execvp");
                _exit(1);
            }else{ // pid del padre
                // El padre espera a que el hijo termine
                waitpid(nvo_pid, NULL, 0);   
            }
        }
    }
}

int main(){
    //aqui se instalan manejadores de señales
    instalar_handlers();
    minishell();
    return 0;
}
