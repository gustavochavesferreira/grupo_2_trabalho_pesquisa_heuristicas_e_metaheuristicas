#ifndef EMPACOTADOR_BASE_H
#define EMPACOTADOR_BASE_H

#include "decodificador.h"
#include <random>

using namespace std;

struct ResultadoEmpacotaBase {
    int64_t area_total = 0;
    int64_t excesso_area = 0;
    vector<ResultadoDecodificacao> tentativas;
    int indice_melhor = -1;
    bool contabilizado = false;
};

bool melhora_empacotamento(const ResultadoDecodificacao& candidata, const ResultadoDecodificacao& atual);
ResultadoEmpacotaBase empacota_base(const Instancia& instancia, const vector<int64_t>& pecas, mt19937& gerador,
                                  const vector<int64_t>& sequencia_anterior = {}, size_t indice_chapa = 0, CronometroCpu* relogio = nullptr);

#endif
