#include "apresentacao.h"

#include <ostream>

void apresenta_projeto(std::ostream& saida) {
    saida << "TP3 - Corte de Estoque Bidimensional com rotação de 90 graus\n"
          << "Configurações propostas: Hbase, Hext, Hint e Hcomb.\n"
          << "Controle auxiliar: Haleat. Comparadora da literatura: RLS-f7.\n"
          << "Estado: estrutura inicial; heurísticas ainda não implementadas.\n";
}
