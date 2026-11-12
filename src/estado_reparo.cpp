#include "estado_reparo.h"

#include <algorithm>
#include <stdexcept>
#include <tuple>
#include <utility>
#include <unordered_map>

using namespace std;

Inviabilidade calcula_inviabilidade(const EstadoReparo& estado) {
    Inviabilidade total;
    for (const ChapaReparo& chapa : estado.chapas) {
        total.excesso_area += chapa.empacotamento.excesso_area;
        total.area_rejeitada += chapa.resultado.area_rejeitada;
        total.pecas_rejeitadas += static_cast<int64_t>(chapa.resultado.rejeitadas.size());
        if (chapa.empacotamento.excesso_area > 0 || !chapa.resultado.rejeitadas.empty()) total.chapas_inviaveis++;
    }
    return total;
}

bool menor_inviabilidade(Inviabilidade candidata, Inviabilidade atual) {
    return tie(candidata.excesso_area, candidata.area_rejeitada, candidata.chapas_inviaveis, candidata.pecas_rejeitadas) <
           tie(atual.excesso_area, atual.area_rejeitada, atual.chapas_inviaveis, atual.pecas_rejeitadas);
}

bool melhora_estado(const EstadoReparo& candidato, const EstadoReparo& atual) {
    return menor_inviabilidade(calcula_inviabilidade(candidato), calcula_inviabilidade(atual));
}

EstadoReparo cria_estado_reparo(const Instancia& instancia, const Solucao& solucao) {
    auto verificacao = verifica_solucao(instancia, solucao);
    if (!verificacao.valido) throw invalid_argument("Solução de origem inválida: " + verificacao.erro);
    EstadoReparo estado;
    for (const Chapa& chapa : solucao.chapas) {
        ChapaReparo reparo;
        reparo.resultado.chapa = chapa;
        for (Posicionamento p : chapa.posicionamentos) {
            reparo.pecas.push_back(p.copia_id);
            reparo.empacotamento.area_total += p.largura * p.altura;
        }
        reparo.resultado.sequencia = reparo.pecas;
        estado.chapas.push_back(reparo);
    }
    return estado;
}

void reempacota_chapa(const Instancia& instancia, EstadoReparo& estado, size_t indice, mt19937& gerador, CronometroCpu* relogio, MecanismosBusca* mecanismos) {
    ChapaReparo& chapa = estado.chapas.at(indice);
    auto anterior = chapa.resultado.sequencia;
    auto empacotamento = empacota_base(instancia, chapa.pecas, gerador, anterior, indice, relogio);
    if (mecanismos != nullptr && mecanismos->eventos != nullptr) mecanismos->eventos->push_back(empacotamento.tentativas.empty() ? "excesso_area" : "tentativas_basicas");
    if (mecanismos != nullptr && mecanismos->orientacao_externa) atualiza_historico(instancia, chapa.pecas, empacotamento, mecanismos->historico);
    if (mecanismos != nullptr && mecanismos->eventos != nullptr && empacotamento.contabilizado) mecanismos->eventos->push_back("historico_atualizado");
    ResultadoDecodificacao resultado;
    if (empacotamento.indice_melhor >= 0) {
        resultado = empacotamento.tentativas[empacotamento.indice_melhor];
        if (mecanismos != nullptr && mecanismos->orientacao_interna && !resultado.rejeitadas.empty()) {
            if (mecanismos->eventos != nullptr) mecanismos->eventos->push_back("busca_interna");
            if (mecanismos->controle_aleatorio) resultado = busca_interna_aleatoria(instancia, resultado, indice, mecanismos->metricas_internas, gerador, relogio);
            else resultado = busca_interna(instancia, resultado, indice, mecanismos->metricas_internas, relogio);
        }
    } else {
        // Sem decodificação por excesso de área: não se inventam rejeições nem posições.
        resultado.sequencia = anterior;
    }
    chapa.empacotamento = move(empacotamento);
    chapa.resultado = move(resultado);
}

EstadoReparo remove_e_redistribui(const Instancia& instancia, const Solucao& solucao, mt19937& gerador, CronometroCpu* relogio, MecanismosBusca* mecanismos) {
    verifica_tempo(relogio);
    auto estado = cria_estado_reparo(instancia, solucao);
    if (estado.chapas.size() < 2) throw invalid_argument("Remoção exige pelo menos duas chapas.");
    size_t removida = 0;
    for (size_t c = 1; c < estado.chapas.size(); c++) {
        if (estado.chapas[c].empacotamento.area_total < estado.chapas[removida].empacotamento.area_total) removida = c;
    }
    auto redistribuidas = estado.chapas[removida].pecas;
    estado.chapas.erase(estado.chapas.begin() + removida);
    for (size_t c = 0; c < estado.chapas.size(); c++) {
        for (auto& p : estado.chapas[c].resultado.chapa.posicionamentos) p.indice_chapa = c;
    }
    unordered_map<int64_t, TipoPeca> tipos;
    for (CopiaPeca copia : instancia.copias) tipos.emplace(copia.id, instancia.tipos[copia.indice_tipo]);
    sort(redistribuidas.begin(), redistribuidas.end(), [&](int64_t a, int64_t b) {
        TipoPeca ta = tipos.at(a), tb = tipos.at(b);
        return make_tuple(ta.largura * ta.altura, max(ta.largura, ta.altura), min(ta.largura, ta.altura), a) >
               make_tuple(tb.largura * tb.altura, max(tb.largura, tb.altura), min(tb.largura, tb.altura), b);
    });
    vector<bool> alteradas(estado.chapas.size(), false);
    for (int64_t id : redistribuidas) {
        TipoPeca tipo = tipos.at(id);
        int64_t area = tipo.largura * tipo.altura;
        size_t receptora = 0;
        auto criterio = [&](size_t c) {
            int64_t nova_area = estado.chapas[c].empacotamento.area_total + area;
            return make_tuple(max(int64_t{0}, nova_area - instancia.area_chapa), max(int64_t{0}, instancia.area_chapa - nova_area), c);
        };
        for (size_t c = 1; c < estado.chapas.size(); c++) {
            if (criterio(c) < criterio(receptora)) receptora = c;
        }
        estado.chapas[receptora].pecas.push_back(id);
        estado.chapas[receptora].empacotamento.area_total += area;
        alteradas[receptora] = true;
    }
    for (size_t c = 0; c < estado.chapas.size(); c++) {
        if (alteradas[c]) reempacota_chapa(instancia, estado, c, gerador, relogio, mecanismos);
    }
    return estado;
}

Solucao solucao_do_reparo(const Instancia& instancia, const EstadoReparo& estado) {
    auto inviabilidade = calcula_inviabilidade(estado);
    if (inviabilidade.excesso_area != 0 || inviabilidade.area_rejeitada != 0 || inviabilidade.chapas_inviaveis != 0 || inviabilidade.pecas_rejeitadas != 0) {
        throw invalid_argument("Estado de reparo ainda inviável.");
    }
    Solucao solucao;
    for (size_t c = 0; c < estado.chapas.size(); c++) {
        const ChapaReparo& chapa = estado.chapas[c];
        auto atribuicoes = chapa.pecas;
        vector<int64_t> posicionadas;
        for (Posicionamento p : chapa.resultado.chapa.posicionamentos) posicionadas.push_back(p.copia_id);
        sort(atribuicoes.begin(), atribuicoes.end());
        sort(posicionadas.begin(), posicionadas.end());
        if (atribuicoes != posicionadas) throw invalid_argument("Atribuições diferem das cópias posicionadas.");
        if (atribuicoes.empty()) continue;
        Chapa usada = chapa.resultado.chapa;
        for (auto& p : usada.posicionamentos) {
            if (p.indice_chapa != c) throw invalid_argument("Índice de chapa inconsistente no reparo.");
            p.indice_chapa = solucao.chapas.size();
        }
        solucao.chapas.push_back(usada);
    }
    auto verificacao = verifica_solucao(instancia, solucao);
    if (!verificacao.valido) throw invalid_argument("Reparo não produz solução válida: " + verificacao.erro);
    return solucao;
}
