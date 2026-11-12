#include "orientacao_interna.h"

#include <stdexcept>
#include <algorithm>

using namespace std;

vector<int64_t> altera_sequencia(const vector<int64_t>& sequencia, MovimentoInterno movimento) {
    if (movimento.origem >= sequencia.size() || movimento.destino >= movimento.origem) throw invalid_argument("Movimento interno deve antecipar uma cópia.");
    auto candidata = sequencia;
    if (movimento.troca) {
        swap(candidata[movimento.origem], candidata[movimento.destino]);
    } else {
        int64_t id = candidata[movimento.origem];
        candidata.erase(candidata.begin() + movimento.origem);
        candidata.insert(candidata.begin() + movimento.destino, id);
    }
    return candidata;
}

ResultadoDecodificacao busca_interna_impl(const Instancia& instancia, const ResultadoDecodificacao& inicial, size_t indice_chapa,
                                    MetricasInternas& metricas, CronometroCpu* relogio, vector<MovimentoInterno>* registro, mt19937* gerador) {
    auto atual = inicial;
    if (atual.rejeitadas.empty()) return atual;
    metricas.ativacoes++;
    size_t adicionais = 0;
    while (!atual.rejeitadas.empty() && adicionais < 16) {
        if (atual.posicao_primeira_rejeitada <= 0 || static_cast<uint64_t>(atual.posicao_primeira_rejeitada) >= atual.sequencia.size()) throw invalid_argument("Primeira rejeição inválida para a busca interna.");
        size_t origem = static_cast<size_t>(atual.posicao_primeira_rejeitada);
        if (gerador != nullptr) {
            uniform_int_distribution<size_t> sorteio(1, atual.sequencia.size() - 1);
            origem = sorteio(*gerador);
        }
        vector<size_t> destinos;
        for (size_t d = origem; d > 0; d--) destinos.push_back(d - 1);
        if (gerador != nullptr) shuffle(destinos.begin(), destinos.end(), *gerador);
        if (destinos.size() > 8) destinos.resize(8);
        bool melhorou = false;
        for (bool troca : {false, true}) {
            for (size_t destino : destinos) {
                if (adicionais == 16) break;
                verifica_tempo(relogio);
                MovimentoInterno movimento{origem, destino, troca};
                auto sequencia = altera_sequencia(atual.sequencia, movimento);
                auto candidata = decodifica_inferior_esquerdo(instancia, sequencia, indice_chapa, relogio);
                adicionais++;
                metricas.decodificacoes++;
                if (registro != nullptr) registro->push_back(movimento);
                if (melhora_empacotamento(candidata, atual)) {
                    atual = candidata;
                    metricas.melhorias++;
                    melhorou = true;
                    break;
                }
            }
            if (melhorou) break;
        }
        if (!melhorou) break;
    }
    if (atual.rejeitadas.empty()) metricas.completos++;
    return atual;
}

ResultadoDecodificacao busca_interna(const Instancia& instancia, const ResultadoDecodificacao& inicial, size_t indice_chapa,
                                    MetricasInternas& metricas, CronometroCpu* relogio, vector<MovimentoInterno>* registro) {
    return busca_interna_impl(instancia, inicial, indice_chapa, metricas, relogio, registro, nullptr);
}

ResultadoDecodificacao busca_interna_aleatoria(const Instancia& instancia, const ResultadoDecodificacao& inicial, size_t indice_chapa,
                                              MetricasInternas& metricas, mt19937& gerador, CronometroCpu* relogio, vector<MovimentoInterno>* registro) {
    return busca_interna_impl(instancia, inicial, indice_chapa, metricas, relogio, registro, &gerador);
}
