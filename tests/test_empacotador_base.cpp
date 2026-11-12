#include "empacotador_base.h"

#include <algorithm>
#include <iostream>
#include <set>
#include <stdexcept>
#include <tuple>

using namespace std;

void exige(bool ok, string motivo) {
    if (!ok) throw runtime_error(motivo);
}

Instancia cria_instancia(int64_t w, int64_t h, vector<pair<int64_t, int64_t>> dimensoes) {
    Instancia instancia;
    instancia.largura = w;
    instancia.altura = h;
    instancia.area_chapa = w * h;
    for (auto dimensao : dimensoes) {
        int64_t id = static_cast<int64_t>(instancia.tipos.size()) + 1;
        instancia.copias.push_back({id, instancia.tipos.size()});
        instancia.tipos.push_back({id, dimensao.first, dimensao.second, 1, 0, 0});
        instancia.area_total += dimensao.first * dimensao.second;
    }
    return instancia;
}

void verifica_tentativas(const Instancia& instancia, const ResultadoEmpacotaBase& resultado) {
    exige(resultado.tentativas.size() == 8 && resultado.indice_melhor >= 0 && resultado.indice_melhor < 8, "Não executou oito tentativas.");
    for (int i = 0; i < 8; i++) {
        const ResultadoDecodificacao& t = resultado.tentativas[i];
        Solucao completa;
        if (!t.chapa.posicionamentos.empty()) completa.chapas.push_back(t.chapa);
        for (int64_t id : t.rejeitadas) {
            TipoPeca tipo = instancia.tipos[id - 1];
            completa.chapas.push_back(Chapa{{{id, completa.chapas.size(), 0, 0, tipo.largura, tipo.altura, false}}});
        }
        exige(verifica_solucao(instancia, completa).valido, "Tentativa perdeu/duplicou peças ou produziu geometria inválida.");
        auto melhor = resultado.tentativas[resultado.indice_melhor];
        exige(!melhora_empacotamento(t, melhor), "Selecionou tentativa pior.");
        if (!melhora_empacotamento(melhor, t)) exige(resultado.indice_melhor <= i, "Empate não preservou a primeira tentativa.");
    }
}

int main() {
    mt19937 gerador(1001);
    auto inicial = gerador;
    auto excesso = cria_instancia(2, 2, {{2, 2}, {1, 1}});
    auto r = empacota_base(excesso, {1, 2}, gerador);
    exige(r.area_total == 5 && r.excesso_area == 1 && r.tentativas.empty() && r.indice_melhor == -1, "Descarte por área incorreto.");
    exige(gerador == inicial, "Descarte por área consumiu aleatoriedade.");
    auto grande = le_instancia("tests/data/area_64bits.txt");
    r = empacota_base(grande, {1, 2}, gerador);
    exige(r.excesso_area == 10000000000LL && r.tentativas.empty(), "Excesso de área truncado.");
    auto instancia = cria_instancia(20, 20, {{2, 6}, {3, 4}, {2, 2}, {2, 6}});
    r = empacota_base(instancia, {3, 1, 4, 2}, gerador);
    exige(r.tentativas[0].sequencia == vector<int64_t>({4, 1, 2, 3}), "Ordenação por área, lados e ID incorreta.");
    verifica_tentativas(instancia, r);
    exige(r.indice_melhor == 0, "Empate entre completas não preservou primeira.");
    auto a = empacota_base(instancia, {1, 2, 3}, gerador, {4, 3, 1});
    exige(a.tentativas[7].sequencia == vector<int64_t>({3, 1, 2}), "Atualização não removeu saída/preservou ordem/anexou entrada.");
    auto b = empacota_base(instancia, {1, 2, 3}, gerador, {4});
    exige(b.tentativas[7].sequencia == vector<int64_t>({1, 2, 3}), "Sequência anterior sem interseção atualizada incorretamente.");
    auto indexada = empacota_base(instancia, {1}, gerador, {}, 5);
    for (auto tentativa : indexada.tentativas) exige(tentativa.chapa.posicionamentos[0].indice_chapa == 5, "Índice da chapa não preservado.");
    auto impossivel = cria_instancia(5, 4, {{3, 3}, {3, 3}});
    r = empacota_base(impossivel, {1, 2}, gerador);
    verifica_tentativas(impossivel, r);
    exige(r.tentativas[0].area_rejeitada == 9 && r.indice_melhor == 0, "Falha geométrica ou desempate incorreto.");
    ResultadoDecodificacao t1, t2;
    t1.area_rejeitada = 5; t1.rejeitadas = {1, 2};
    t2.area_rejeitada = 6; t2.rejeitadas = {1};
    exige(melhora_empacotamento(t1, t2), "Área deve preceder quantidade.");
    t2.area_rejeitada = 5;
    exige(melhora_empacotamento(t2, t1), "Quantidade não desempata área.");
    exige(!melhora_empacotamento(t1, t1), "Comparação não é estrita.");
    for (vector<int64_t> invalida : {vector<int64_t>{1, 1}, vector<int64_t>{999}}) {
        bool recusou = false;
        try { empacota_base(instancia, invalida, gerador); }
        catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Conjunto inválido aceito.");
        recusou = false;
        try { empacota_base(instancia, {1, 2}, gerador, invalida); }
        catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Sequência anterior inválida aceita.");
    }
    r = empacota_base(instancia, {}, gerador);
    exige(r.tentativas.size() == 8 && r.indice_melhor == 0 && r.area_total == 0, "Conjunto vazio incorreto.");

    mt19937 dados(1002);
    for (int teste = 0; teste < 80; teste++) {
        vector<pair<int64_t, int64_t>> dimensoes;
        for (int i = 0; i < 7; i++) dimensoes.push_back({1 + dados() % 3, 1 + dados() % 3});
        auto pequena = cria_instancia(6, 6, dimensoes);
        if (pequena.area_total > pequena.area_chapa) continue;
        vector<int64_t> ids{1, 2, 3, 4, 5, 6, 7};
        mt19937 g1(1001), g2(1001);
        auto x = empacota_base(pequena, ids, g1);
        auto y = empacota_base(pequena, ids, g2);
        verifica_tentativas(pequena, x);
        exige(g1 == g2 && x.indice_melhor == y.indice_melhor, "Estado aleatório ou escolha não reproduzível.");
        for (int i = 0; i < 8; i++) {
            auto tx = x.tentativas[i]; auto ty = y.tentativas[i];
            exige(tx.sequencia == ty.sequencia && tx.rejeitadas == ty.rejeitadas && tx.area_rejeitada == ty.area_rejeitada, "Tentativa não reproduzível.");
            for (size_t j = 0; j < tx.chapa.posicionamentos.size(); j++) {
                auto px = tx.chapa.posicionamentos[j]; auto py = ty.chapa.posicionamentos[j];
                exige(tie(px.x, px.y, px.rotacionada) == tie(py.x, py.y, py.rotacionada), "Posicionamento não reproduzível.");
            }
            if (i == 0) continue;
            auto restantes = x.tentativas[0].sequencia;
            for (int64_t id : tx.sequencia) {
                auto pos = find(restantes.begin(), restantes.end(), id);
                exige(pos != restantes.end() && pos - restantes.begin() < 3, "Sorteio fora das ceil(sqrt(7)) maiores restantes.");
                restantes.erase(pos);
            }
        }
    }
    cout << "Empacotador-base: oito tentativas, área, ordem, histórico de sequência, seleção e reprodução: OK\n";
}
