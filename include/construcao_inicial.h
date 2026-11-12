#ifndef CONSTRUCAO_INICIAL_H
#define CONSTRUCAO_INICIAL_H

#include "solucao.h"
#include "tempo_cpu.h"

using namespace std;

Solucao constroi_solucao_inicial(const Instancia& instancia, CronometroCpu* relogio = nullptr);

#endif
