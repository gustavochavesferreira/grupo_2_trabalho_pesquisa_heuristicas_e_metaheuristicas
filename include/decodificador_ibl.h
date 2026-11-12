#ifndef DECODIFICADOR_IBL_H
#define DECODIFICADOR_IBL_H

#include "solucao.h"
#include "tempo_cpu.h"

using namespace std;

struct ResultadoIBL {
    Solucao solucao;
    int64_t area_perfil = 0;
    // Área da chapa vezes K pode ultrapassar 64 bits, mesmo com área demandada válida.
    __uint128_t f7 = 0;
};

Posicionamento posiciona_ibl(Posicionamento p, const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio = nullptr);
int64_t area_perfil_superior(const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio = nullptr);
__uint128_t calcula_f7(int64_t area_chapa, size_t chapas, int64_t area_perfil);
ResultadoIBL decodifica_ibl(const Instancia& instancia, const vector<int64_t>& permutacao, CronometroCpu* relogio = nullptr);

#endif
