#ifndef VND_H
#define VND_H

#include "estado_reparo.h"
#include <array>

using namespace std;

struct MovimentoExterno {
    int vizinhanca = 1;
    size_t origem = 0;
    size_t receptora = 0;
    int64_t base = -1;
    int64_t parceiro = -1;
};

struct ResultadoVizinhanca {
    EstadoReparo estado;
    vector<int64_t> bases;
    size_t avaliados = 0;
    bool melhorou = false;
    MovimentoExterno escolhido;
};

struct ResultadoVnd {
    EstadoReparo estado;
    array<size_t, 3> avaliacoes{};
    array<size_t, 3> melhorias{};
    size_t reinicios = 0;
};

size_t escolhe_origem(const EstadoReparo& estado);
vector<int64_t> amostra_bases_uniforme(const EstadoReparo& estado, size_t origem, size_t total_copias, mt19937& gerador);
MovimentoExterno cria_movimento(const Instancia& instancia, const EstadoReparo& estado, size_t origem, int64_t base, int vizinhanca, mt19937& gerador);
EstadoReparo aplica_movimento(const Instancia& instancia, const EstadoReparo& estado, MovimentoExterno movimento, mt19937& gerador);
ResultadoVizinhanca explora_vizinhanca(const Instancia& instancia, const EstadoReparo& estado, int vizinhanca, mt19937& gerador);
ResultadoVnd executa_vnd(const Instancia& instancia, const EstadoReparo& estado, mt19937& gerador);

#endif
