#include "hbase.h"

#include <set>
#include <iostream>
#include <stdexcept>

using namespace std;
void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

int main() {
    Instancia i;
    i.largura = 5; i.altura = 4; i.area_chapa = 20; i.area_total = 18;
    i.tipos = {{1,3,3,2,0,0}}; i.copias = {{1,0},{2,0}};
    mt19937 g(1001);
    auto r = empacota_base(i, {1,2}, g);
    HistoricoExterno h;
    atualiza_historico(i, {1,2}, r, h);
    auto chave = composicao_chapa(i, {2,1});
    exige(chave == vector<int64_t>{2} && r.contabilizado, "Composição ou marcação incorreta.");
    exige(h.dados.at(chave)[0].oportunidades == 16 && h.dados.at(chave)[0].rejeicoes == 8, "O e F incorretos para demandas repetidas.");
    auto copia = r;
    atualiza_historico(i, {1,2}, r, h); atualiza_historico(i, {1,2}, copia, h);
    exige(h.metricas.atualizacoes == 1 && h.dados.at(chave)[0].oportunidades == 16, "Contou novamente tentativas copiadas/consultadas.");
    exige(peso_externo(i, chave, 1, h) == 1.5 && peso_externo(i, vector<int64_t>{1}, 1, h) == 1, "Peso F/O incorreto ou vazamento entre composições.");
    mt19937 a(1002), b(1002);
    auto sa = amostra_bases_ponderada(i, {1,2}, 2, h, a);
    auto sb = amostra_bases_ponderada(i, {1,2}, 2, h, b);
    exige(sa == sb && set<int64_t>(sa.begin(), sa.end()).size() == 2 && h.metricas.atualizacoes == 1, "Amostragem alterou contagens ou repetiu cópias.");
    auto completa = empacota_base(i, {1}, g);
    atualiza_historico(i, {1}, completa, h);
    exige(!completa.contabilizado && h.metricas.atualizacoes == 1, "Contou chamada completa.");
    i.area_chapa = 10;
    auto excesso = empacota_base(i, {1,2}, g);
    atualiza_historico(i, {1,2}, excesso, h);
    exige(!excesso.contabilizado && h.metricas.atualizacoes == 1, "Contou excesso de área.");
    reinicia_historico(h);
    exige(h.dados.empty() && peso_externo(i, chave, 1, h) == 1 && h.metricas.reinicios == 1, "Reinício não limpou pesos.");
    i = le_instancia("tests/data/valida.txt");
    auto final = executa_hext(i, 1001, 10);
    exige(final.metodo == "Hext" && verifica_solucao(i, final.solucao).valido, "Hext não integrada ou inválida.");
    // Uma redução com excesso de área reinicia o histórico, mas não o alimenta.
    Instancia falha;
    falha.largura = 10; falha.altura = 1; falha.area_chapa = 10; falha.area_total = 18;
    falha.tipos = {{1,6,1,3,0,0}}; falha.copias = {{1,0},{2,0},{3,0}};
    auto f = executa_hext(falha, 1001, 10);
    exige(f.orientacao_externa.reinicios == f.tentativas_reducao && f.orientacao_externa.atualizacoes == 0 && f.tentativas_reducao == 1, "Histórico não atualizado/reiniciado no ponto correto.");
    // Exercita a seleção ponderada no VND sem contabilizar novamente o resultado.
    falha.largura = 5; falha.altura = 4; falha.area_chapa = 20; falha.area_total = 18;
    falha.tipos = {{1,3,3,2,0,0}}; falha.copias = {{1,0},{2,0}};
    falha.tipos.push_back({2,1,1,1,0,0}); falha.copias.push_back({3,1}); falha.area_total++;
    EstadoReparo e; e.chapas.resize(2); e.chapas[0].pecas = {1,2}; e.chapas[1].pecas = {3};
    MecanismosBusca m; m.orientacao_externa = true;
    reempacota_chapa(falha, e, 0, g, nullptr, &m); reempacota_chapa(falha, e, 1, g, nullptr, &m);
    auto antes = m.historico.metricas.atualizacoes;
    auto passo = explora_vizinhanca(falha, e, 1, g, nullptr, nullptr, &m);
    exige(passo.avaliados == 2 && m.historico.metricas.movimentos_orientados == 2, "Não registrou movimentos ponderados.");
    exige(m.historico.metricas.atualizacoes >= antes, "Histórico regrediu.");
    cout << "Hext: contagem única, composições, pesos, amostragem, reinício e integração: OK\n";
}
