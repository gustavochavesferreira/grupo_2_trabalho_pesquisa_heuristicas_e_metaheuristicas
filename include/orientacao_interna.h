#ifndef ORIENTACAO_INTERNA_H
#define ORIENTACAO_INTERNA_H

#include "empacotador_base.h"

using namespace std;

struct MetricasInternas {
    size_t ativacoes = 0;
    size_t decodificacoes = 0;
    size_t melhorias = 0;
    size_t completos = 0;
};

struct MovimentoInterno {
    size_t origem;
    size_t destino;
    bool troca;
};

vector<int64_t> altera_sequencia(const vector<int64_t>& sequencia, MovimentoInterno movimento);
ResultadoDecodificacao busca_interna(const Instancia& instancia, const ResultadoDecodificacao& inicial, size_t indice_chapa,
                                    MetricasInternas& metricas, CronometroCpu* relogio = nullptr, vector<MovimentoInterno>* registro = nullptr);

ResultadoDecodificacao busca_interna_aleatoria(const Instancia& instancia, const ResultadoDecodificacao& inicial, size_t indice_chapa,
                                              MetricasInternas& metricas, mt19937& gerador, CronometroCpu* relogio = nullptr,
                                              vector<MovimentoInterno>* registro = nullptr);

#endif
