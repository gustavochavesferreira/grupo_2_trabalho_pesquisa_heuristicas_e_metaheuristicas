#include "hbase.h"
#include "construcao_inicial.h"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>

using namespace std;

EstadoReparo perturba_estado(const Instancia& instancia, const EstadoReparo& estado, size_t quantidade_chapas, mt19937& gerador, CronometroCpu* relogio) {
    if (quantidade_chapas < 2 || estado.chapas.size() < 2) throw invalid_argument("Perturbação exige duas ou mais chapas.");
    verifica_tempo(relogio);
    auto candidato = estado;
    vector<size_t> selecionadas(estado.chapas.size());
    iota(selecionadas.begin(), selecionadas.end(), 0);
    size_t quantidade = min(quantidade_chapas, selecionadas.size());
    for (size_t i = 0; i < quantidade; i++) {
        uniform_int_distribution<size_t> sorteio(i, selecionadas.size() - 1);
        swap(selecionadas[i], selecionadas[sorteio(gerador)]);
    }
    selecionadas.resize(quantidade);
    sort(selecionadas.begin(), selecionadas.end());
    vector<int64_t> pecas;
    for (size_t c : selecionadas) {
        pecas.insert(pecas.end(), candidato.chapas[c].pecas.begin(), candidato.chapas[c].pecas.end());
        candidato.chapas[c].pecas.clear();
    }
    shuffle(pecas.begin(), pecas.end(), gerador);
    // Um deslocamento sorteado e a distribuição circular garantem destinos distintos
    // quando há pelo menos duas peças, sem criar chapas ou restringir a inviabilidade.
    uniform_int_distribution<size_t> inicio(0, quantidade - 1);
    size_t deslocamento = inicio(gerador);
    for (size_t i = 0; i < pecas.size(); i++) candidato.chapas[selecionadas[(i + deslocamento) % quantidade]].pecas.push_back(pecas[i]);
    for (size_t c : selecionadas) reempacota_chapa(instancia, candidato, c, gerador, relogio);
    return candidato;
}

bool aceita_reducao(const Instancia& instancia, const EstadoReparo& estado, ResultadoHbase& resultado, CronometroCpu& relogio) {
    if (calcula_inviabilidade(estado).chapas_inviaveis != 0) return false;
    auto candidata = solucao_do_reparo(instancia, estado);
    if (candidata.chapas.size() >= resultado.solucao.chapas.size()) throw runtime_error("Reparo não reduziu o número de chapas.");
    resultado.solucao = candidata;
    resultado.reducoes_aceitas++;
    resultado.tempo_melhor = relogio.decorrido();
    return true;
}

ResultadoHbase executa_hbase(const Instancia& instancia, uint32_t semente, double limite_cpu, ConfigHbase config) {
    CronometroCpu relogio(limite_cpu);
    if (config.chapas_perturbadas < 2) throw invalid_argument("Configure pelo menos duas chapas perturbadas.");
    mt19937 gerador(semente);
    ResultadoHbase resultado;
    // Sem solução inicial completa não há resultado factível para devolver.
    resultado.solucao = constroi_solucao_inicial(instancia, &relogio);
    resultado.tempo_melhor = relogio.decorrido();
    resultado.limites = calcula_limites(instancia);
    resultado.motivo_parada = "orcamento_reparo";
    OrcamentoVnd orcamento{config.max_avaliacoes_reparo, 0};
    size_t acumuladas = 0;
    try {
        while (static_cast<int64_t>(resultado.solucao.chapas.size()) > resultado.limites.referencia) {
            relogio.verifica();
            if (config.max_avaliacoes_reparo == 0) break;
            resultado.tentativas_reducao++;
            auto estado = remove_e_redistribui(instancia, resultado.solucao, gerador, &relogio);
            size_t reinicios = 0;
            bool reduziu = false;
            // O orçamento é compartilhado por todas as descidas desta redução.
            while (true) {
                relogio.verifica();
                auto descida = executa_vnd(instancia, estado, gerador, &relogio, &orcamento);
                estado = descida.estado;
                if (aceita_reducao(instancia, estado, resultado, relogio)) { reduziu = true; break; }
                if (descida.limite_reparo || reinicios >= config.max_reinicios || estado.chapas.size() < 2) break;
                relogio.verifica();
                auto perturbado = perturba_estado(instancia, estado, config.chapas_perturbadas, gerador, &relogio);
                resultado.perturbacoes++;
                reinicios++;
                auto reparado = executa_vnd(instancia, perturbado, gerador, &relogio, &orcamento);
                if (melhora_estado(reparado.estado, estado)) estado = reparado.estado;
                if (aceita_reducao(instancia, estado, resultado, relogio)) { reduziu = true; break; }
                if (reparado.limite_reparo) break;
            }
            acumuladas += orcamento.usadas;
            orcamento.usadas = 0;
            if (!reduziu) break;
        }
    } catch (const TempoEsgotado&) {
        resultado.motivo_parada = "limite_cpu";
    }
    if (static_cast<int64_t>(resultado.solucao.chapas.size()) == resultado.limites.referencia) resultado.motivo_parada = "limite_inferior";
    else if (relogio.esgotado()) resultado.motivo_parada = "limite_cpu";
    resultado.avaliacoes = acumuladas + orcamento.usadas;
    auto verificacao = verifica_solucao(instancia, resultado.solucao);
    if (!verificacao.valido) throw runtime_error("Hbase terminou com solução inválida: " + verificacao.erro);
    resultado.tempo_total = relogio.decorrido();
    return resultado;
}
