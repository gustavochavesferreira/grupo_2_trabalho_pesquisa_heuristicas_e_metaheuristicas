#include "rls.h"

#include <algorithm>
#include <limits>
#include <stdexcept>

using namespace std;

vector<int64_t> permutacao_inicial_rls(const Instancia& instancia, mt19937& gerador, CronometroCpu* relogio) {
    verifica_tempo(relogio);
    vector<int64_t> permutacao;
    for (auto copia : instancia.copias) {
        verifica_tempo(relogio);
        permutacao.push_back(instancia.tipos.at(copia.indice_tipo).id);
    }
    shuffle(permutacao.begin(), permutacao.end(), gerador);
    bernoulli_distribution sinal(0.5);
    for (auto& valor : permutacao) {
        verifica_tempo(relogio);
        if (sinal(gerador)) valor = -valor;
    }
    return permutacao;
}

MovimentoRls sorteia_movimento_rls(const vector<int64_t>& permutacao, mt19937& gerador, CronometroCpu* relogio) {
    verifica_tempo(relogio);
    if (permutacao.empty()) throw invalid_argument("Movimento RLS exige uma permutação não vazia.");
    uniform_int_distribution<size_t> posicao(0, permutacao.size() - 1);
    bernoulli_distribution tenta_troca(0.5);
    MovimentoRls movimento;
    movimento.primeira = posicao(gerador);
    movimento.segunda = movimento.primeira;
    if (tenta_troca(gerador)) {
        uint64_t max_sorteios = 10 * static_cast<uint64_t>(permutacao.size());
        for (uint64_t tentativa = 0; tentativa < max_sorteios; tentativa++) {
            verifica_tempo(relogio);
            movimento.segunda = posicao(gerador);
            movimento.sorteios_parceiro++;
            if (permutacao[movimento.segunda] != permutacao[movimento.primeira]) {
                movimento.troca = true;
                break;
            }
        }
    }
    return movimento;
}

void aplica_movimento_rls(vector<int64_t>& permutacao, MovimentoRls movimento) {
    int64_t valor = permutacao.at(movimento.primeira);
    if (movimento.troca) {
        if (permutacao.at(movimento.segunda) == valor) throw invalid_argument("Troca RLS exige valores assinados diferentes.");
        swap(permutacao[movimento.primeira], permutacao[movimento.segunda]);
    } else {
        if (valor == 0 || valor == numeric_limits<int64_t>::min()) throw invalid_argument("Valor inválido para inversão de sinal.");
        permutacao[movimento.primeira] = -valor;
    }
}

bool aceita_rls(__uint128_t candidata, __uint128_t atual) { return candidata <= atual; }

vector<MarcoRls> evolucao_rls(const vector<pair<double, int64_t>>& melhorias, int64_t limite_referencia) {
    return calcula_evolucao(melhorias, limite_referencia);
}

ResultadoRls executa_rls(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigRls config) {
    CronometroCpu relogio(limite_cpu);
    if (config.max_avaliacoes == 0 || config.max_avaliacoes > 100000000) throw invalid_argument("RLS permite de 1 a 100000000 avaliações, incluindo a inicial.");
    mt19937 gerador(semente);
    ResultadoRls resultado;
    resultado.permutacao = permutacao_inicial_rls(instancia, gerador, &relogio);
    DecodificadorIbl decodificador(instancia);
    ResultadoIBL atual, empacotamento;
    decodificador.decodifica(resultado.permutacao, nullptr, 0, numeric_limits<size_t>::max(), atual, &relogio);
    resultado.avaliacoes = 1;
    resultado.tempo_melhor = relogio.decorrido();
    vector<pair<double, int64_t>> melhorias{{resultado.tempo_melhor, static_cast<int64_t>(atual.solucao.chapas.size())}};
    resultado.limites = calcula_limites(instancia);
    resultado.motivo_parada = "limite_avaliacoes";
    try {
        while (static_cast<int64_t>(atual.solucao.chapas.size()) > resultado.limites.referencia && resultado.avaliacoes < config.max_avaliacoes) {
            relogio.verifica();
            auto candidata = resultado.permutacao;
            auto movimento = sorteia_movimento_rls(candidata, gerador, &relogio);
            aplica_movimento_rls(candidata, movimento);
            if (movimento.troca) resultado.trocas++;
            else resultado.inversoes++;
            // As posições antes da primeira alterada não mudam: o IBL recomeça dali.
            size_t inicio = movimento.troca ? min(movimento.primeira, movimento.segunda) : movimento.primeira;
            // Com mais chapas que a atual, f7 é estritamente maior e o candidato seria rejeitado.
            bool completo = decodificador.decodifica(candidata, &atual, inicio, atual.solucao.chapas.size(), empacotamento, &relogio);
            resultado.avaliacoes++;
            // Um candidato que atravessa o prazo não substitui a última solução aceita.
            relogio.verifica();
            if (completo && aceita_rls(empacotamento.f7, atual.f7)) {
                resultado.aceitos++;
                if (empacotamento.f7 < atual.f7) resultado.melhorias++;
                bool reduziu = empacotamento.solucao.chapas.size() < atual.solucao.chapas.size();
                swap(atual, empacotamento);
                resultado.permutacao = move(candidata);
                if (reduziu) {
                    resultado.tempo_melhor = relogio.decorrido();
                    melhorias.push_back({resultado.tempo_melhor, static_cast<int64_t>(atual.solucao.chapas.size())});
                }
            }
        }
    } catch (const TempoEsgotado&) {
        resultado.motivo_parada = "limite_cpu";
    }
    if (static_cast<int64_t>(atual.solucao.chapas.size()) == resultado.limites.referencia) resultado.motivo_parada = "limite_inferior";
    resultado.solucao = move(atual.solucao);
    resultado.area_perfil = atual.area_perfil;
    resultado.f7 = atual.f7;
    auto verificacao = verifica_solucao(instancia, resultado.solucao);
    if (!verificacao.valido) throw runtime_error("RLS terminou com solução inválida: " + verificacao.erro);
    resultado.evolucao = evolucao_rls(melhorias, resultado.limites.referencia);
    resultado.tempo_total = relogio.decorrido();
    if (resultado.motivo_parada != "limite_inferior" && resultado.tempo_total >= limite_cpu) resultado.motivo_parada = "limite_cpu";
    return resultado;
}
