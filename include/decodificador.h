#ifndef DECODIFICADOR_H
#define DECODIFICADOR_H

#include "geometria.h"

using namespace std;

struct ResultadoDecodificacao {
    vector<int64_t> sequencia;
    Chapa chapa;
    vector<int64_t> rejeitadas;
    int64_t primeira_rejeitada = -1;
    int64_t posicao_primeira_rejeitada = -1;
    int64_t area_rejeitada = 0;
};

// A sequência pode ser um subconjunto de cópias, sem repetições.
ResultadoDecodificacao decodifica_inferior_esquerdo(const Instancia& instancia, const vector<int64_t>& sequencia, size_t indice_chapa = 0);

#endif
