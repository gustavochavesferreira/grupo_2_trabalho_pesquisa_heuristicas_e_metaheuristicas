#include "hbase.h"

#include <iostream>
#include <stdexcept>

using namespace std;
void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

int main() {
    Instancia i; i.largura = 8; i.altura = 7; i.area_chapa = 56;
    vector<pair<int64_t,int64_t>> dimensoes{{3,1},{2,2},{4,2},{4,3},{3,3},{2,2},{2,5},{2,3}};
    vector<int64_t> ids;
    for (auto d : dimensoes) {
        int64_t id = static_cast<int64_t>(i.tipos.size()) + 1;
        i.copias.push_back({id,i.tipos.size()}); i.tipos.push_back({id,d.first,d.second,1,0,0}); i.area_total += d.first*d.second; ids.push_back(id);
    }
    mt19937 g(1001);
    auto base = empacota_base(i, ids, g);
    exige(!base.tentativas[base.indice_melhor].rejeitadas.empty(), "Caso deveria falhar nas oito tentativas básicas.");
    HistoricoExterno esperado;
    atualiza_historico(i, ids, base, esperado);
    vector<string> eventos;
    MecanismosBusca m; m.orientacao_externa = true; m.orientacao_interna = true; m.eventos = &eventos;
    EstadoReparo estado; estado.chapas.resize(1); estado.chapas[0].pecas = ids;
    mt19937 mesma(1001); reempacota_chapa(i, estado, 0, mesma, nullptr, &m);
    exige(eventos == vector<string>({"tentativas_basicas","historico_atualizado","busca_interna"}), "Ordem dos eventos de Hcomb incorreta.");
    exige(m.historico.metricas.atualizacoes == 1 && estado.chapas[0].empacotamento.contabilizado, "Não contabilizou uma única vez.");
    exige(m.metricas_internas.decodificacoes == 11 && m.metricas_internas.completos == 1, "Não executou Hint após o histórico.");
    auto chave = composicao_chapa(i, ids);
    for (size_t t = 0; t < i.tipos.size(); t++) {
        auto real = m.historico.dados.at(chave)[t], ref = esperado.dados.at(chave)[t];
        exige(real.oportunidades == ref.oportunidades && real.rejeicoes == ref.rejeicoes, "Decodificações adicionais alteraram o histórico básico.");
        exige(real.oportunidades == 8, "Oportunidades extras contadas indevidamente.");
    }
    auto duplicada = estado.chapas[0].empacotamento;
    atualiza_historico(i, ids, duplicada, m.historico);
    atualiza_historico(i, ids, estado.chapas[0].empacotamento, m.historico);
    exige(m.historico.metricas.atualizacoes == 1, "Consulta/cópia posterior recontou tentativas.");
    exige(verifica_solucao(i, solucao_do_reparo(i, estado)).valido, "Hcomb não produziu empacotamento completo válido.");
    // Mesma semente e componentes: Hext mantém a mesma informação básica usada por Hcomb.
    MecanismosBusca externa; externa.orientacao_externa = true;
    EstadoReparo sem_interna; sem_interna.chapas.resize(1); sem_interna.chapas[0].pecas = ids;
    mt19937 outro(1001); reempacota_chapa(i, sem_interna, 0, outro, nullptr, &externa);
    exige(sem_interna.chapas[0].resultado.area_rejeitada > 0 && !estado.chapas[0].resultado.area_rejeitada, "Mecanismo interno não foi isolado.");
    for (size_t t = 0; t < i.tipos.size(); t++) exige(externa.historico.dados.at(chave)[t].rejeicoes == m.historico.dados.at(chave)[t].rejeicoes, "Hext e Hcomb receberam histórico diferente das mesmas tentativas.");
    auto resultado = executa_hcomb(i, 1001, 10);
    auto repetido = executa_hcomb(i, 1001, 10);
    exige(resultado.metodo == "Hcomb" && !resultado.controle_auxiliar && verifica_solucao(i, resultado.solucao).valido, "Hcomb não integrada ou inválida.");
    exige(resultado.solucao.chapas.size() == repetido.solucao.chapas.size() && resultado.avaliacoes == repetido.avaliacoes && resultado.orientacao_interna.decodificacoes == repetido.orientacao_interna.decodificacoes && resultado.orientacao_externa.atualizacoes == repetido.orientacao_externa.atualizacoes, "Hcomb não reproduzível.");
    // Excesso de área não ativa histórico nem busca interna.
    auto menor = i; menor.largura = 7; menor.altura = 7; menor.area_chapa = 49;
    EstadoReparo excesso; excesso.chapas.resize(1); excesso.chapas[0].pecas = ids;
    MecanismosBusca nenhum; nenhum.orientacao_externa = true; nenhum.orientacao_interna = true;
    reempacota_chapa(menor, excesso, 0, g, nullptr, &nenhum);
    exige(nenhum.historico.metricas.atualizacoes == 0 && nenhum.metricas_internas.ativacoes == 0, "Hcomb ativou mecanismos em excesso de área.");
    cout << "Hcomb: ordem dos eventos, histórico básico único, extras separados, integração e reprodução: OK\n";
}
