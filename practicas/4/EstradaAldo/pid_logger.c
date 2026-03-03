#include <stdio.h>
#include <process.h>

int main() {
    FILE *f = fopen("salida_proceso.txt", "w");
    if (!f) {
        perror("fopen");
        return 1;
    }
    
    fprintf(f, "PID=%d\n", _getpid());
    fclose(f);
    
    printf("Listo: genere salida_proceso.txt\n");
    return 0;
}
