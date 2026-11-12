#ifndef INSTANCIA_H
#define INSTANCIA_H

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

struct TipoPeca {
    std::int64_t id;
    std::int64_t largura;
    std::int64_t altura;
    std::int64_t demanda;
    std::int64_t limite_copias;
    double lucro;
};

struct CopiaPeca {
    std::int64_t id;
    std::size_t indice_tipo;
};

struct Instancia {
    std::string caminho;
    std::int64_t largura = 0;
    std::int64_t altura = 0;
    std::int64_t area_chapa = 0;
    std::int64_t area_total = 0;
    std::vector<TipoPeca> tipos;
    std::vector<CopiaPeca> copias;
};

// Retorna apenas instâncias completas; erros de entrada geram std::runtime_error.
Instancia le_instancia(const std::string& caminho);

#endif
