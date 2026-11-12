#include "rls.h"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>

using namespace std;

void exige(bool ok, string erro) { if (!ok) throw runtime_error(erro); }

Instancia linha(vector<int64_t> larguras) {
    Instancia i; i.largura = 10; i.altura = 1; i.area_chapa = 10;
    for (int64_t w : larguras) {
        int64_t id = static_cast<int64_t>(i.tipos.size()) + 1;
        i.tipos.push_back({id,w,1,1,0,0}); i.copias.push_back({id,i.tipos.size()-1}); i.area_total += w;
    }
    return i;
}

string retrato(const Solucao& s) {
    ostringstream texto;
    for (const auto& chapa : s.chapas) {
        texto << '[';
        for (auto p : chapa.posicionamentos) texto << p.copia_id << ',' << p.x << ',' << p.y << ',' << p.largura << ',' << p.altura << ',' << p.rotacionada << ';';
        texto << ']';
    }
    return texto.str();
}

int main() {
    auto i = le_instancia("tests/data/valida.txt");
    map<int64_t, int64_t> demanda;
    for (auto t : i.tipos) demanda[t.id] = t.demanda;
    bool positivo = false, negativo = false;
    for (uint32_t s = 1001; s <= 1030; s++) {
        mt19937 a(s), b(s);
        auto pa = permutacao_inicial_rls(i, a), pb = permutacao_inicial_rls(i, b);
        exige(pa == pb && a == b && pa.size() == i.copias.size(), "Inicialização não reproduzível.");
        map<int64_t, int64_t> contagem;
        for (auto v : pa) { contagem[v < 0 ? -v : v]++; positivo |= v > 0; negativo |= v < 0; }
        exige(contagem == demanda, "Inicialização usa cópias no lugar de repetições de tipos.");
    }
    exige(positivo && negativo, "Inicialização não sorteou os sinais.");
    bool troca = false, inversao = false, falha_troca = false, troca_sinais = false;
    for (uint32_t s = 1; s <= 200; s++) {
        vector<int64_t> pi{1,-1,2,2};
        mt19937 a(s), b(s);
        auto ma = sorteia_movimento_rls(pi, a), mb = sorteia_movimento_rls(pi, b);
        exige(ma.primeira == mb.primeira && ma.segunda == mb.segunda && ma.troca == mb.troca && ma.sorteios_parceiro == mb.sorteios_parceiro && a == b, "Movimento não reproduzível.");
        exige(ma.sorteios_parceiro <= 40 && (!ma.troca || pi[ma.primeira] != pi[ma.segunda]), "Troca desrespeitou o teto ou o valor assinado.");
        auto original = pi;
        aplica_movimento_rls(pi, ma);
        if (ma.troca) {
            troca = true;
            troca_sinais |= abs(original[ma.primeira]) == abs(original[ma.segunda]);
            for (size_t j = 0; j < pi.size(); j++) exige(pi[j] == original[j == ma.primeira ? ma.segunda : j == ma.segunda ? ma.primeira : j], "Troca alterou outras posições.");
        } else {
            inversao = true;
            for (size_t j = 0; j < pi.size(); j++) exige(pi[j] == (j == ma.primeira ? -original[j] : original[j]), "Inversão alterou outras posições.");
        }
        vector<int64_t> iguais{1,1,1};
        auto m = sorteia_movimento_rls(iguais, a);
        exige(!m.troca && (m.sorteios_parceiro == 0 || m.sorteios_parceiro == 30), "Não usou exatamente 10T sorteios antes da inversão por falta de parceiro.");
        falha_troca |= m.sorteios_parceiro == 30;
        aplica_movimento_rls(iguais, m);
        exige(count(iguais.begin(), iguais.end(), -1) == 1, "Fallback não inverteu um sinal.");
        vector<int64_t> unica{1};
        auto so = sorteia_movimento_rls(unica, b); aplica_movimento_rls(unica, so);
        exige(unica[0] == -1 && !so.troca && (so.sorteios_parceiro == 0 || so.sorteios_parceiro == 10), "Movimento com T=1 incorreto.");
    }
    exige(troca && inversao && falha_troca && troca_sinais, "Testes não exercitaram os dois operadores e seus casos especiais.");
    __uint128_t grande = static_cast<__uint128_t>(numeric_limits<uint64_t>::max()) + 100;
    exige(aceita_rls(grande, grande) && aceita_rls(grande-1, grande) && !aceita_rls(grande+1, grande), "Aceitação não respeita <= f7 exato.");
    exige(ConfigRls{}.max_avaliacoes == 100000000, "Teto publicado alterado.");
    auto impossivel = linha({6,6,6});
    auto r = executa_rls(impossivel, 1001, 10, {64});
    exige(r.metodo == "RLS-f7" && r.avaliacoes == 64 && r.aceitos == 63 && r.melhorias == 0 && r.trocas+r.inversoes == 63, "Teto de avaliações, inclusão da inicial ou aceitação de empates incorreta.");
    exige(r.motivo_parada == "limite_avaliacoes" && r.solucao.chapas.size() == 3 && r.limites.referencia == 2 && r.f7 == 26, "Resultado/parada por avaliações incorreto.");
    exige(verifica_solucao(impossivel, r.solucao).valido && retrato(r.solucao) == retrato(decodifica_ibl(impossivel, r.permutacao).solucao), "Solução e genótipo finais divergentes.");
    auto uma = executa_rls(impossivel, 1001, 10, {1});
    exige(uma.avaliacoes == 1 && uma.trocas+uma.inversoes == 0 && uma.aceitos == 0, "Orçamento unitário não preservou a avaliação inicial.");
    auto lb = executa_rls(linha({6,4}), 1001, 10);
    exige(lb.motivo_parada == "limite_inferior" && lb.avaliacoes == 1 && lb.solucao.chapas.size() == 1 && verifica_solucao(linha({6,4}), lb.solucao).valido, "Não parou quando a inicial atingiu LBref.");
    // Reprodução com orçamento de operações, incluindo casos de redução e rejeição.
    uint64_t reducoes = 0, rejeitados = 0, melhorias = 0;
    auto busca = linha({4,4,3,3,3,3});
    for (uint32_t s = 1001; s <= 1030; s++) {
        auto a = executa_rls(busca, s, 10, {80}), b = executa_rls(busca, s, 10, {80});
        exige(a.permutacao == b.permutacao && a.f7 == b.f7 && a.avaliacoes == b.avaliacoes && a.aceitos == b.aceitos && a.melhorias == b.melhorias && a.trocas == b.trocas && retrato(a.solucao) == retrato(b.solucao), "RLS não reproduzível com a mesma semente/orçamento.");
        exige(verifica_solucao(busca, a.solucao).valido && a.tempo_melhor >= 0 && a.tempo_melhor <= a.tempo_total, "Factibilidade ou tempos inconsistentes.");
        mt19937 g(s);
        auto inicial = decodifica_ibl(busca, permutacao_inicial_rls(busca, g));
        exige(a.f7 <= inicial.f7 && a.solucao.chapas.size() <= inicial.solucao.chapas.size(), "Busca piorou a solução inicial.");
        reducoes += inicial.solucao.chapas.size() - a.solucao.chapas.size();
        rejeitados += a.avaliacoes - 1 - a.aceitos;
        melhorias += a.melhorias;
        if (a.solucao.chapas.size() == static_cast<size_t>(a.limites.referencia)) exige(a.motivo_parada == "limite_inferior", "Continuou buscando após LBref.");
    }
    exige(reducoes > 0 && rejeitados > 0 && melhorias > 0, "Casos de integração não exercitaram redução, rejeição e melhoria.");
    // Marcos exatos: não usar uma melhoria posterior ao tempo pedido nem inventar inicial.
    auto marcos = evolucao_rls({{0.2,4},{1.0,3},{7.0,2}}, 2);
    exige(marcos.size() == 6 && !marcos[0].disponivel && marcos[0].chapas == 0, "Inventou solução anterior à construção.");
    exige(marcos[1].tempo == 1 && marcos[1].chapas == 3 && marcos[1].desvio == 50 && marcos[2].chapas == 3 && marcos[3].chapas == 2 && marcos[4].chapas == 2 && marcos[5].chapas == 2, "Evolução usa eventos futuros ou perdeu a parada antecipada.");
    exige(r.evolucao.size() == 6, "Execução não retornou os marcos.");
    for (auto marco : r.evolucao) exige(marco.disponivel && marco.chapas == 3 && marco.desvio == 50, "Evolução da execução com K constante incorreta.");
    auto cpu = executa_rls(impossivel, 1001, 0.025);
    exige(cpu.motivo_parada == "limite_cpu" && cpu.tempo_total >= 0.025 && cpu.avaliacoes <= 100000000 && verifica_solucao(impossivel, cpu.solucao).valido, "Parada por CPU incorreta ou perdeu incumbente.");
    bool parou = false;
    try { executa_rls(impossivel, 1001, 0); } catch (const TempoEsgotado&) { parou = true; }
    exige(parou, "Sem tempo para a inicial, retornou solução parcial.");
    for (uint64_t invalido : {uint64_t{0}, uint64_t{100000001}}) {
        bool recusou = false;
        try { executa_rls(impossivel, 1001, 10, {invalido}); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Aceitou teto de avaliações inválido.");
    }
    for (double invalido : {-1.0, numeric_limits<double>::infinity(), numeric_limits<double>::quiet_NaN()}) {
        bool recusou = false;
        try { executa_rls(impossivel, 1001, invalido); } catch (const invalid_argument&) { recusou = true; }
        exige(recusou, "Aceitou limite de CPU inválido.");
    }
    for (string nome : {"valida.txt", "area_64bits.txt", "espacos_crlf.txt"}) {
        auto bidimensional = le_instancia("tests/data/"+nome);
        auto final = executa_rls(bidimensional, 1001, 10, {40});
        exige(verifica_solucao(bidimensional, final.solucao).valido && decodifica_ibl(bidimensional, final.permutacao).f7 == final.f7, "RLS inválida nos casos bidimensionais.");
    }
    cout << "RLS-f7: repetições/sinais, operadores, fallback 10T, aceitação, 30 sementes, avaliações, LBref, CPU e evolução: OK\n";
}
