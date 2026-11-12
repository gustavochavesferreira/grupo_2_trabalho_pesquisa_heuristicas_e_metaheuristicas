#ifndef INSTANCIA_H
#define INSTANCIA_H

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

using namespace std;

struct TipoPeca {
    int64_t id;
    int64_t largura;
    int64_t altura;
    int64_t demanda;
    int64_t limite_copias;
    double lucro;
};

struct CopiaPeca {
    int64_t id;
    size_t indice_tipo;
};

struct Instancia {
    string caminho;
    int64_t largura = 0;
    int64_t altura = 0;
    int64_t area_chapa = 0;
    int64_t area_total = 0;
    vector<TipoPeca> tipos;
    vector<CopiaPeca> copias;
};

// Retorna apenas instâncias completas; erros de entrada geram runtime_error.
Instancia le_instancia(string caminho);

#endif
