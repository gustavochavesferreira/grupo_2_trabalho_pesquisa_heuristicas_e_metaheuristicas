#include "instancia.h"

#include <exception>
#include <iostream>

int main(int argc, char* argv[]) {
    try {
        for (int i = 1; i < argc; ++i) {
            auto instancia = le_instancia(argv[i]);
            std::cout << instancia.tipos.size() << ',' << instancia.copias.size() << ','
                      << instancia.largura << ',' << instancia.altura << '\n';
        }
    } catch (const std::exception& erro) {
        std::cerr << erro.what() << '\n';
        return 1;
    }
    return 0;
}
