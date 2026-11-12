#include "instancia.h"

#include <exception>
#include <iostream>

using namespace std;

int main(int argc, char* argv[]) {
    try {
        for (int i = 1; i < argc; ++i) {
            auto instancia = le_instancia(argv[i]);
            cout << instancia.tipos.size() << ',' << instancia.copias.size() << ','
                      << instancia.largura << ',' << instancia.altura << '\n';
        }
    } catch (const exception& erro) {
        cerr << erro.what() << '\n';
        return 1;
    }
    return 0;
}
