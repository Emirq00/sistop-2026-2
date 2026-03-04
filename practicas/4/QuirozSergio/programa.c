#include <stdio.h>

int main() {
    FILE *f = fopen("salida.txt", "w");
    fprintf(f, "Este archivo fue generado automáticamente\n");
    fclose(f);

    printf("Archivo generado correctamente\n");
    return 0;
}
