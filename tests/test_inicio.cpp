#include "apresentacao.h"

#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

int main() {
    std::ostringstream saida;
    apresenta_projeto(saida);
    std::string texto = saida.str();

    // A apresentação deve distinguir as propostas dos controles e informar o estágio real.
    for (const std::string trecho : {"TP3", "Hbase, Hext, Hint e Hcomb", "Controle auxiliar: Haleat", "Comparadora da literatura: RLS-f7", "heurísticas ainda não implementadas"}) {
        if (texto.find(trecho) == std::string::npos) {
            throw std::runtime_error("Apresentação incompleta: " + trecho);
        }
    }

    if (texto.empty() || texto.back() != '\n') {
        throw std::runtime_error("A apresentação deve terminar com uma quebra de linha.");
    }

    std::cout << "Teste da apresentação inicial: OK\n";
    return 0;
}
