#include "hbase.h"

#include <algorithm>
#include <iostream>
#include <stdexcept>

using namespace std;
void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

int main() {
    Instancia i; i.largura = 10; i.altura = 10; i.area_chapa = 100; i.area_total = 90;
    i.tipos = {{1,3,3,10,0,0}};
    vector<int64_t> ids;
    for (int64_t id = 1; id <= 10; id++) { i.copias.push_back({id,0}); ids.push_back(id); }
    auto incompleta = decodifica_inferior_esquerdo(i, ids);
    bool variou = false;
    for (uint32_t semente = 1001; semente <= 1030; semente++) {
        mt19937 a(semente), b(semente);
        MetricasInternas ma, mb; vector<MovimentoInterno> ra, rb;
        auto x = busca_interna_aleatoria(i, incompleta, 0, ma, a, nullptr, &ra);
        auto y = busca_interna_aleatoria(i, incompleta, 0, mb, b, nullptr, &rb);
        exige(a == b && x.sequencia == y.sequencia && ra.size() == rb.size() && ma.decodificacoes == mb.decodificacoes, "Busca aleatória não reproduzível.");
        exige(ma.ativacoes == 1 && ma.decodificacoes > 0 && ma.decodificacoes <= 16 && ma.melhorias == 0 && ma.completos == 0, "Orçamento/métricas diferem do controle esperado.");
        for (size_t n = 0; n < ra.size(); n++) {
            exige(ra[n].origem == rb[n].origem && ra[n].destino == rb[n].destino && ra[n].troca == rb[n].troca, "Movimentos aleatórios não reproduzíveis.");
            auto seq = altera_sequencia(incompleta.sequencia, ra[n]); sort(seq.begin(), seq.end());
            exige(seq == ids, "Movimento aleatório perdeu/duplicou cópias.");
            if (ra[n].origem != 9 || ra[n].destino != 8 - n % 8) variou = true;
        }
    }
    exige(variou, "Controle aleatório imitou a orientação pela primeira rejeição.");
    ConfigHbase config; config.max_reinicios = 1;
    auto a = executa_haleat(i, 1001, 10, config);
    auto b = executa_haleat(i, 1001, 10, config);
    exige(a.metodo == "Haleat" && a.controle_auxiliar && a.orientacao_externa.atualizacoes == 0, "Controle não identificado ou criou histórico.");
    exige(a.solucao.chapas.size() == b.solucao.chapas.size() && a.avaliacoes == b.avaliacoes && a.orientacao_interna.decodificacoes == b.orientacao_interna.decodificacoes, "Execução auxiliar não reproduzível.");
    exige(a.orientacao_interna.ativacoes > 0 && verifica_solucao(i, a.solucao).valido, "Haleat não ativou ou produziu solução inválida.");
    cout << "Haleat: mesmo orçamento/operadores, escolhas aleatórias, 30 sementes e integração reproduzível: OK\n";
}
