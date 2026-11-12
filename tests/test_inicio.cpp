#include "apresentacao.h"

#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

using namespace std;

int main() {
    ostringstream saida;
    apresenta_projeto(saida);
    string texto = saida.str();

    // A apresentação deve distinguir as propostas dos controles e informar o estágio real.
    for (string trecho : {"TP3", "Hbase, Hext, Hint e Hcomb", "Controle auxiliar: Haleat", "Comparadora da literatura: RLS-f7", "Hbase, Hext, Hint, Hcomb, Haleat e RLS-f7 disponíveis na biblioteca C++", "interface experimental ainda não implementada"}) {
        if (texto.find(trecho) == string::npos) {
            throw runtime_error("Apresentação incompleta: " + trecho);
        }
    }

    if (texto.empty() || texto.back() != '\n') {
        throw runtime_error("A apresentação deve terminar com uma quebra de linha.");
    }

    cout << "Teste da apresentação inicial: OK\n";
    return 0;
}
