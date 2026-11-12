#ifndef GEOMETRIA_H
#define GEOMETRIA_H

#include "solucao.h"
#include "tempo_cpu.h"

using namespace std;

struct PontoCanto {
    int64_t x;
    int64_t y;
};

bool contido_na_chapa(Posicionamento p, int64_t largura, int64_t altura);
bool sobrepoe(Posicionamento a, Posicionamento b);
bool posicao_livre(Posicionamento p, const Chapa& chapa, int64_t largura, int64_t altura);
void coordenadas_canto(const Chapa& chapa, int64_t largura, int64_t altura, vector<int64_t>& xs, vector<int64_t>& ys);
vector<PontoCanto> pontos_canto(const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio = nullptr);

#endif
