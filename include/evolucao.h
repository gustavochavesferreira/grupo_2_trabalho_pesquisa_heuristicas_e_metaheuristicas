#ifndef EVOLUCAO_H
#define EVOLUCAO_H

#include <cstdint>
#include <utility>
#include <vector>

using namespace std;

struct MarcoEvolucao {
    double tempo = 0;
    bool disponivel = false;
    int64_t chapas = 0;
    double desvio = 0;
};

vector<MarcoEvolucao> calcula_evolucao(const vector<pair<double, int64_t>>& melhorias, int64_t limite_referencia);

#endif
