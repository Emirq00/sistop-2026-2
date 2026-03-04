#include <iostream>
#include <cstdlib>  

using namespace std;

int main() {
    cout << "Padre: creando proceso hijo..." << endl;

    system("cmd /C echo Hola desde el proceso hijo");

    cout << "Padre: el proceso hijo terminó." << endl;

    return 0;
}
