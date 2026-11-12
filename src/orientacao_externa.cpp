#include "orientacao_externa.h"

#include <algorithm>

using namespace std;

vector<int64_t> composicao_chapa(const Instancia& instancia, const vector<int64_t>& pecas) {
    vector<int64_t> composicao(instancia.tipos.size(), 0);
    for (int64_t id : pecas) composicao.at(instancia.copias.at(static_cast<size_t>(id - 1)).indice_tipo)++;
    return composicao;
}

void reinicia_historico(HistoricoExterno& historico) {
    historico.dados.clear();
    historico.metricas.reinicios++;
}

void atualiza_historico(const Instancia& instancia, const vector<int64_t>& pecas, ResultadoEmpacotaBase& tentativas, HistoricoExterno& historico) {
    if (tentativas.contabilizado || tentativas.excesso_area > 0 || tentativas.area_total > instancia.area_chapa || tentativas.tentativas.size() != 8) return;
    for (const auto& tentativa : tentativas.tentativas) if (tentativa.rejeitadas.empty()) return;
    auto composicao = composicao_chapa(instancia, pecas);
    auto& contagens = historico.dados[composicao];
    if (contagens.empty()) contagens.resize(instancia.tipos.size());
    for (const auto& tentativa : tentativas.tentativas) {
        for (size_t t = 0; t < composicao.size(); t++) contagens[t].oportunidades += composicao[t];
        for (int64_t id : tentativa.rejeitadas) contagens.at(instancia.copias.at(static_cast<size_t>(id - 1)).indice_tipo).rejeicoes++;
    }
    tentativas.contabilizado = true;
    historico.metricas.atualizacoes++;
}

double peso_externo(const Instancia& instancia, const vector<int64_t>& composicao, int64_t copia, const HistoricoExterno& historico) {
    auto encontrada = historico.dados.find(composicao);
    if (encontrada == historico.dados.end()) return 1;
    auto t = instancia.copias.at(static_cast<size_t>(copia - 1)).indice_tipo;
    auto contagem = encontrada->second.at(t);
    return 1 + static_cast<double>(contagem.rejeicoes) / max(uint64_t{1}, contagem.oportunidades);
}

vector<int64_t> amostra_bases_ponderada(const Instancia& instancia, const vector<int64_t>& pecas, size_t quantidade, HistoricoExterno& historico, mt19937& gerador) {
    auto composicao = composicao_chapa(instancia, pecas);
    auto restantes = pecas;
    vector<double> pesos;
    for (int64_t id : restantes) pesos.push_back(peso_externo(instancia, composicao, id, historico));
    vector<int64_t> amostra;
    while (amostra.size() < quantidade && !restantes.empty()) {
        discrete_distribution<size_t> sorteio(pesos.begin(), pesos.end());
        size_t posicao = sorteio(gerador);
        amostra.push_back(restantes[posicao]);
        restantes.erase(restantes.begin() + posicao);
        pesos.erase(pesos.begin() + posicao);
    }
    return amostra;
}
