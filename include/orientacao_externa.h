#ifndef ORIENTACAO_EXTERNA_H
#define ORIENTACAO_EXTERNA_H

#include "empacotador_base.h"
#include "orientacao_interna.h"
#include <map>

using namespace std;

struct ContagemRejeicoes {
    uint64_t oportunidades = 0;
    uint64_t rejeicoes = 0;
};

struct MetricasExternas {
    size_t atualizacoes = 0;
    size_t reinicios = 0;
    size_t movimentos_orientados = 0;
    size_t melhorias_aceitas = 0;
};

struct HistoricoExterno {
    map<vector<int64_t>, vector<ContagemRejeicoes>> dados;
    MetricasExternas metricas;
};

struct MecanismosBusca {
    bool orientacao_externa = false;
    bool orientacao_interna = false;
    bool controle_aleatorio = false;
    MetricasInternas metricas_internas;
    vector<string>* eventos = nullptr;
    HistoricoExterno historico;
};

vector<int64_t> composicao_chapa(const Instancia& instancia, const vector<int64_t>& pecas);
void reinicia_historico(HistoricoExterno& historico);
void atualiza_historico(const Instancia& instancia, const vector<int64_t>& pecas, ResultadoEmpacotaBase& tentativas, HistoricoExterno& historico);
double peso_externo(const Instancia& instancia, const vector<int64_t>& composicao, int64_t copia, const HistoricoExterno& historico);
vector<int64_t> amostra_bases_ponderada(const Instancia& instancia, const vector<int64_t>& pecas, size_t quantidade, HistoricoExterno& historico, mt19937& gerador);

#endif
