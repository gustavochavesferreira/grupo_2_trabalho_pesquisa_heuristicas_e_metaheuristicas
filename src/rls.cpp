#include "rls.h"
#include "construcao_inicial.h"

#include <algorithm>
#include <tuple>
#include <unordered_map>
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

vector<int64_t> permutacao_da_solucao(const Instancia& instancia, const Solucao& solucao, mt19937& gerador,
                                      uint64_t tentativas_por_chapa, uint64_t limite, uint64_t& avaliacoes,
                                      CronometroCpu* relogio) {
    unordered_map<int64_t, size_t> tipo_da_copia;
    for (auto copia : instancia.copias) tipo_da_copia.emplace(copia.id, copia.indice_tipo);
    vector<int64_t> permutacao;
    for (const auto& chapa : solucao.chapas) {
        verifica_tempo(relogio);
        auto ps = chapa.posicionamentos;
        auto assina = [&](const vector<Posicionamento>& ordem) {
            vector<int64_t> v;
            for (const auto& p : ordem) {
                int64_t id = instancia.tipos.at(tipo_da_copia.at(p.copia_id)).id;
                v.push_back(p.rotacionada ? -id : id);
            }
            return v;
        };
        // Ordens fixas: inserção da gulosa, (y, x), (x, y), altura e área decrescentes.
        vector<vector<int64_t>> fixas{assina(ps)};
        stable_sort(ps.begin(), ps.end(), [](const auto& a, const auto& b) { return tie(a.y, a.x) < tie(b.y, b.x); });
        fixas.push_back(assina(ps));
        auto por_yx = fixas.back();
        auto copia = ps;
        stable_sort(copia.begin(), copia.end(), [](const auto& a, const auto& b) { return tie(a.x, a.y) < tie(b.x, b.y); });
        fixas.push_back(assina(copia));
        stable_sort(copia.begin(), copia.end(), [](const auto& a, const auto& b) { return a.altura > b.altura; });
        fixas.push_back(assina(copia));
        stable_sort(copia.begin(), copia.end(), [](const auto& a, const auto& b) { return a.largura * a.altura > b.largura * b.altura; });
        fixas.push_back(assina(copia));
        // Subinstância só com as cópias desta chapa: o IBL exige a demanda completa.
        Instancia sub = instancia;
        sub.copias.clear();
        sub.area_total = 0;
        for (auto& t : sub.tipos) t.demanda = 0;
        for (const auto& p : chapa.posicionamentos) {
            size_t t = tipo_da_copia.at(p.copia_id);
            sub.copias.push_back({p.copia_id, t});
            sub.tipos[t].demanda++;
            sub.area_total += p.largura * p.altura;
        }
        DecodificadorIbl decodificador(sub);
        ResultadoIBL rascunho;
        vector<int64_t> escolhida = por_yx;
        bernoulli_distribution sinal(0.5);
        for (uint64_t k = 0; k < tentativas_por_chapa && avaliacoes < limite; k++) {
            vector<int64_t> candidata;
            if (k < fixas.size()) candidata = fixas[k];
            else {
                candidata = por_yx;
                shuffle(candidata.begin(), candidata.end(), gerador);
                for (auto& v : candidata) if (sinal(gerador)) v = -v;
            }
            avaliacoes++;
            if (decodificador.decodifica(candidata, nullptr, 0, 1, rascunho, relogio)) { escolhida = move(candidata); break; }
        }
        permutacao.insert(permutacao.end(), escolhida.begin(), escolhida.end());
    }
    if (permutacao.size() != instancia.copias.size()) throw invalid_argument("Solução não contém toda a demanda.");
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
    // Variante gulosa: a construção gulosa é a incumbente; a busca parte da permutação
    // induzida por ela (o IBL nem sempre a reproduz) e só a substitui se a superar.
    Solucao incumbente;
    if (config.inicial_gulosa) {
        incumbente = constroi_solucao_inicial(instancia, &relogio);
        resultado.permutacao = permutacao_da_solucao(instancia, incumbente, gerador, config.tentativas_por_chapa,
                                                     config.max_avaliacoes - 1, resultado.avaliacoes, &relogio);
    } else {
        resultado.permutacao = permutacao_inicial_rls(instancia, gerador, &relogio);
    }
    DecodificadorIbl decodificador(instancia);
    ResultadoIBL atual, empacotamento;
    decodificador.decodifica(resultado.permutacao, nullptr, 0, numeric_limits<size_t>::max(), atual, &relogio);
    resultado.avaliacoes++;
    resultado.tempo_melhor = relogio.decorrido();
    size_t melhor_k = atual.solucao.chapas.size();
    if (config.inicial_gulosa) melhor_k = min(melhor_k, incumbente.chapas.size());
    vector<pair<double, int64_t>> melhorias{{resultado.tempo_melhor, static_cast<int64_t>(melhor_k)}};
    resultado.limites = calcula_limites(instancia);
    resultado.motivo_parada = "limite_avaliacoes";
    try {
        while (static_cast<int64_t>(melhor_k) > resultado.limites.referencia && resultado.avaliacoes < config.max_avaliacoes) {
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
                // Sem incumbente, melhor_k é sempre o K atual: idêntico à RLS-f7 original.
                bool reduziu = empacotamento.solucao.chapas.size() < melhor_k;
                swap(atual, empacotamento);
                resultado.permutacao = move(candidata);
                if (reduziu) {
                    melhor_k = atual.solucao.chapas.size();
                    resultado.tempo_melhor = relogio.decorrido();
                    melhorias.push_back({resultado.tempo_melhor, static_cast<int64_t>(atual.solucao.chapas.size())});
                }
            }
        }
    } catch (const TempoEsgotado&) {
        resultado.motivo_parada = "limite_cpu";
    }
    resultado.solucao = move(atual.solucao);
    resultado.area_perfil = atual.area_perfil;
    resultado.f7 = atual.f7;
    if (config.inicial_gulosa) {
        int64_t perfil = area_perfil_superior(incumbente.chapas.back(), instancia.largura, instancia.altura);
        __uint128_t f7 = calcula_f7(instancia.area_chapa, incumbente.chapas.size(), perfil);
        // Empate em f7 fica com a solução da busca.
        if (f7 < resultado.f7) { resultado.solucao = move(incumbente); resultado.area_perfil = perfil; resultado.f7 = f7; }
    }
    if (static_cast<int64_t>(resultado.solucao.chapas.size()) == resultado.limites.referencia) resultado.motivo_parada = "limite_inferior";
    auto verificacao = verifica_solucao(instancia, resultado.solucao);
    if (!verificacao.valido) throw runtime_error("RLS terminou com solução inválida: " + verificacao.erro);
    resultado.evolucao = evolucao_rls(melhorias, resultado.limites.referencia);
    resultado.tempo_total = relogio.decorrido();
    if (resultado.motivo_parada != "limite_inferior" && resultado.tempo_total >= limite_cpu) resultado.motivo_parada = "limite_cpu";
    return resultado;
}
