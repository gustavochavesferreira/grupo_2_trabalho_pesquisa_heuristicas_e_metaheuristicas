#ifndef LIMITES_INFERIORES_H
#define LIMITES_INFERIORES_H

#include "instancia.h"

using namespace std;

struct GrupoQuadrados {
    int64_t lado;
    int64_t quantidade;
};

struct LimitesInferiores {
    int64_t por_area;
    int64_t dell_amico;
    int64_t referencia;
};

vector<GrupoQuadrados> decompoe_quadrados(const Instancia& instancia);
int64_t limite_por_area(const Instancia& instancia);
int64_t limite_dell_amico(const Instancia& instancia);
LimitesInferiores calcula_limites(const Instancia& instancia);
double desvio_percentual(int64_t chapas, int64_t limite_referencia);

#endif
