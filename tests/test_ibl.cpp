#include "decodificador_ibl.h"

#include <algorithm>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>

using namespace std;

void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

Instancia exemplo(int64_t w, int64_t h, vector<TipoPeca> tipos) {
    Instancia i; i.largura = w; i.altura = h; i.area_chapa = w*h; i.tipos = tipos;
    for (size_t t = 0; t < tipos.size(); t++) {
        for (int64_t d = 0; d < tipos[t].demanda; d++) i.copias.push_back({static_cast<int64_t>(i.copias.size()) + 1, t});
        i.area_total += tipos[t].largura * tipos[t].altura * tipos[t].demanda;
    }
    return i;
}

bool livre_oraculo(Posicionamento p, const Chapa& chapa) {
    if (p.x < 0 || p.y < 0) return false;
    for (auto q : chapa.posicionamentos) {
        if (p.x < q.x + q.largura && q.x < p.x + p.largura && p.y < q.y + q.altura && q.y < p.y + p.altura) return false;
    }
    return true;
}

// Simulação literal por unidades, sem usar a geometria ou os saltos do IBL.
Solucao oraculo(const Instancia& i, const vector<int64_t>& sequencia) {
    Solucao s; s.chapas.push_back({});
    vector<size_t> usadas(i.tipos.size(), 0);
    for (auto valor : sequencia) {
        size_t t = 0;
        while (i.tipos[t].id != (valor < 0 ? -valor : valor)) t++;
        auto tipo = i.tipos[t];
        bool gira = valor < 0;
        int64_t w = gira ? tipo.altura : tipo.largura, h = gira ? tipo.largura : tipo.altura;
        if (w > i.largura || h > i.altura) { swap(w, h); gira = !gira; }
        vector<int64_t> ids;
        for (auto c : i.copias) if (c.indice_tipo == t) ids.push_back(c.id);
        Posicionamento p{ids[usadas[t]++], s.chapas.size()-1, i.largura-w, i.altura, w, h, gira};
        while (true) {
            auto anterior = p;
            while (true) { auto q = p; q.y--; if (!livre_oraculo(q, s.chapas.back())) break; p = q; }
            while (true) { auto q = p; q.x--; if (!livre_oraculo(q, s.chapas.back())) break; p = q; }
            if (p.x == anterior.x && p.y == anterior.y) break;
        }
        if (p.y + p.altura > i.altura) { s.chapas.push_back({}); p.indice_chapa++; p.x = 0; p.y = 0; }
        s.chapas.back().posicionamentos.push_back(p);
    }
    return s;
}

bool iguais(const Solucao& a, const Solucao& b) {
    if (a.chapas.size() != b.chapas.size()) return false;
    for (size_t c = 0; c < a.chapas.size(); c++) {
        if (a.chapas[c].posicionamentos.size() != b.chapas[c].posicionamentos.size()) return false;
        for (size_t j = 0; j < a.chapas[c].posicionamentos.size(); j++) {
            auto p = a.chapas[c].posicionamentos[j], q = b.chapas[c].posicionamentos[j];
            if (p.copia_id != q.copia_id || p.indice_chapa != q.indice_chapa || p.x != q.x || p.y != q.y || p.largura != q.largura || p.altura != q.altura || p.rotacionada != q.rotacionada) return false;
        }
    }
    return true;
}

int main() {
    // IDs originais fora de ordem, demandas repetidas e correção das duas orientações.
    auto i = exemplo(6, 3, {{2,4,2,2,0,0},{1,2,4,1,0,0}});
    vector<int64_t> seq{-2,1,2};
    auto antes = seq;
    auto r = decodifica_ibl(i, seq);
    exige(seq == antes && r.solucao.chapas.size() == 3 && r.f7 == 44 && r.area_perfil == 8, "Demanda, correção ou f7 manual incorreta.");
    exige(iguais(r.solucao, oraculo(i, seq)) && verifica_solucao(i, r.solucao).valido, "IBL não respeitou repetições/cópias.");
    auto p = r.solucao.chapas[0].posicionamentos[0];
    exige(!p.rotacionada && p.x == 0 && p.y == 0 && p.largura == 4, "Não corrigiu rotação impossível.");
    exige(r.solucao.chapas[1].posicionamentos[0].rotacionada, "Não corrigiu orientação original impossível.");
    // Mantém a chapa corrente: a peça pequena não volta a uma chapa anterior.
    i = exemplo(10, 1, {{1,6,1,2,0,0},{2,4,1,2,0,0}});
    r = decodifica_ibl(i, {1,1,2,2});
    exige(r.solucao.chapas.size() == 3 && r.area_perfil == 4 && r.f7 == 24, "IBL voltou a uma chapa anterior.");
    Chapa degraus{{{1,0,0,0,2,4,false},{2,0,2,0,4,2,false}}};
    p = posiciona_ibl({3,0,0,0,2,2,false}, degraus, 6, 6);
    exige(p.x == 2 && p.y == 2, "Não priorizou descida/contatos.");
    Chapa bloco{{{1,0,4,0,2,3,false}}};
    p = posiciona_ibl({2,0,0,0,2,2,false}, bloco, 6, 6);
    exige(p.x == 0 && p.y == 0, "Não voltou a descer depois de ir à esquerda.");
    Chapa cavidade{{{1,0,0,0,2,2,false},{2,0,2,0,4,1,false},{3,0,2,3,4,1,false}}};
    p = posiciona_ibl({4,0,0,0,2,2,false}, cavidade, 6, 6);
    exige(p.x == 0 && p.y == 2, "IBL substituído por enumeração global de posições.");
    // Perfil inclui vazios sob as peças e usa o máximo, sem somar alturas sobrepostas em x.
    Chapa perfil{{{1,0,0,0,2,2,false},{2,0,0,2,1,3,false},{3,0,3,2,2,1,false}}};
    exige(area_perfil_superior(perfil, 6, 6) == 13 && area_perfil_superior({}, 6, 6) == 0, "Perfil manual incorreto.");
    exige(calcula_f7(36, 2, 13) == 49, "f7 não usa a última chapa.");
    for (int k = 1; k < 5; k++) exige(calcula_f7(36, k, 36) < calcula_f7(36, k+1, 1), "Reduzir K não tem prioridade estrita.");
    // Sem expansão proporcional a W e sem estouro no produto área*K.
    int64_t lado = 3000000000LL;
    i = exemplo(lado, lado, {{1,lado,1,2,0,0},{2,1,lado,2,0,0}});
    r = decodifica_ibl(i, {1,2,1,2});
    exige(r.solucao.chapas.size() == 4 && r.f7 > numeric_limits<uint64_t>::max(), "f7 sofreu estouro de 64 bits.");
    exige(r.f7 == static_cast<__uint128_t>(i.area_chapa)*3 + lado && verifica_solucao(i, r.solucao).valido, "f7 extremo incorreto.");
    i = exemplo(1, numeric_limits<int64_t>::max(), {{1,1,numeric_limits<int64_t>::max(),1,0,0}});
    r = decodifica_ibl(i, {1});
    exige(r.area_perfil == numeric_limits<int64_t>::max(), "Coordenada acima da chapa sofreu estouro.");
    // Comparações com simulação literal e soma coluna a coluna em dimensões pequenas.
    mt19937 g(1001);
    for (int caso = 0; caso < 250; caso++) {
        int64_t w = 2 + g()%8, h = 2 + g()%8;
        vector<TipoPeca> tipos;
        vector<int64_t> sequencia;
        for (int t = 1; t <= 4; t++) {
            int64_t demanda = 1 + g()%3;
            tipos.push_back({t,1 + static_cast<int64_t>(g()%w),1 + static_cast<int64_t>(g()%h),demanda,0,0});
            for (int d = 0; d < demanda; d++) sequencia.push_back(g()%2 ? t : -t);
        }
        i = exemplo(w, h, tipos);
        shuffle(sequencia.begin(), sequencia.end(), g);
        r = decodifica_ibl(i, sequencia);
        exige(iguais(r.solucao, oraculo(i, sequencia)) && verifica_solucao(i, r.solucao).valido, "IBL divergiu do oráculo por unidades.");
        int64_t area = 0;
        for (int64_t x = 0; x < w; x++) {
            int64_t topo = 0;
            for (auto q : r.solucao.chapas.back().posicionamentos) if (q.x <= x && x < q.x+q.largura) topo = max(topo, q.y+q.altura);
            area += topo;
        }
        exige(area == r.area_perfil && r.f7 == static_cast<__uint128_t>(i.area_chapa)*(r.solucao.chapas.size()-1)+area, "Perfil divergiu da soma por colunas.");
    }
    i = exemplo(5, 5, {{1,2,2,2,0,0},{2,1,1,1,0,0}});
    for (vector<int64_t> invalida : vector<vector<int64_t>>{{},{1},{1,1,1},{0,1,2},{1,2,3},{numeric_limits<int64_t>::min(),1,2}}) {
        bool recusou = false;
        try { decodifica_ibl(i, invalida); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Permutação inválida aceita.");
    }
    CronometroCpu zero(0);
    bool parou = false;
    try { decodifica_ibl(i, {1,1,2}, &zero); } catch (const TempoEsgotado&) { parou = true; }
    exige(parou, "IBL ignorou prazo de CPU.");
    cout << "IBL e f7: regras dirigidas, perfil, 250 oráculos, demandas, rotação, CPU e aritmética extrema: OK\n";
}
