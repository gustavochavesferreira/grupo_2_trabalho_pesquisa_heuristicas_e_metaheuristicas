#include "apresentacao.h"

#include <ostream>

using namespace std;

void apresenta_projeto(ostream& saida) {
    saida << "TP3 - Corte de Estoque Bidimensional com rotação de 90 graus\n"
          << "Configurações propostas: Hbase, Hext, Hint e Hcomb.\n"
          << "Controle auxiliar: Haleat. Comparadora da literatura: RLS-f7.\n"
          << "Estado: Hbase, Hext, Hint, Hcomb e Haleat disponíveis na biblioteca C++; interface experimental ainda não implementada.\n";
}
