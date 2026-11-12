#include "estado_reparo.h"
#include "construcao_inicial.h"

#include <algorithm>
#include <iostream>
#include <random>
#include <set>
#include <stdexcept>
#include <tuple>

using namespace std;

void exige(bool ok, string erro) {
    if (!ok) throw runtime_error(erro);
}

Instancia pequena(int64_t w, int64_t h, vector<pair<int64_t, int64_t>> dimensoes) {
    Instancia instancia;
    instancia.largura = w; instancia.altura = h; instancia.area_chapa = w * h;
    for (auto dimensao : dimensoes) {
        auto id = static_cast<int64_t>(instancia.tipos.size()) + 1;
        instancia.copias.push_back({id, instancia.tipos.size()});
        instancia.tipos.push_back({id, dimensao.first, dimensao.second, 1, 0, 0});
        instancia.area_total += dimensao.first * dimensao.second;
    }
    return instancia;
}

void confere(const Instancia& instancia, const EstadoReparo& estado) {
    set<int64_t> atribuidas, colocadas;
    Solucao completa;
    Inviabilidade esperado;
    for (size_t c = 0; c < estado.chapas.size(); c++) {
        const ChapaReparo& chapa = estado.chapas[c];
        int64_t area = 0;
        for (int64_t id : chapa.pecas) {
            exige(atribuidas.insert(id).second, "Cópia duplicada no estado.");
            auto tipo = instancia.tipos.at(instancia.copias.at(id - 1).indice_tipo);
            area += tipo.largura * tipo.altura;
        }
        exige(area == chapa.empacotamento.area_total, "Área da composição incorreta.");
        int64_t excesso = max(int64_t{0}, area - instancia.area_chapa);
        exige(excesso == chapa.empacotamento.excesso_area, "Excesso incorreto.");
        esperado.excesso_area += excesso;
        if (excesso > 0) {
            exige(chapa.empacotamento.tentativas.empty() && chapa.resultado.chapa.posicionamentos.empty(), "Excesso foi decodificado ou preservou posições antigas.");
            exige(chapa.resultado.rejeitadas.empty() && chapa.resultado.area_rejeitada == 0, "Excesso ganhou rejeições fictícias.");
            esperado.chapas_inviaveis++;
        } else {
            int64_t rejeitada = 0;
            for (int64_t id : chapa.resultado.rejeitadas) {
                exige(find(chapa.pecas.begin(), chapa.pecas.end(), id) != chapa.pecas.end(), "Rejeitada não atribuída à chapa.");
                auto tipo = instancia.tipos[instancia.copias[id - 1].indice_tipo];
                rejeitada += tipo.largura * tipo.altura;
            }
            exige(rejeitada == chapa.resultado.area_rejeitada, "Área rejeitada incorreta.");
            esperado.area_rejeitada += rejeitada;
            esperado.pecas_rejeitadas += chapa.resultado.rejeitadas.size();
            if (!chapa.resultado.rejeitadas.empty()) esperado.chapas_inviaveis++;
        }
        if (!chapa.resultado.chapa.posicionamentos.empty()) {
            Chapa copia;
            for (auto p : chapa.resultado.chapa.posicionamentos) {
                exige(p.indice_chapa == c && colocadas.insert(p.copia_id).second, "Índice errado ou cópia colocada duas vezes.");
                p.indice_chapa = completa.chapas.size();
                copia.posicionamentos.push_back(p);
            }
            completa.chapas.push_back(copia);
        }
    }
    exige(atribuidas.size() == instancia.copias.size(), "Cópia perdida.");
    for (auto copia : instancia.copias) {
        exige(atribuidas.count(copia.id), "ID original perdido.");
        if (!colocadas.count(copia.id)) {
            auto tipo = instancia.tipos[copia.indice_tipo];
            bool gira = tipo.largura > instancia.largura || tipo.altura > instancia.altura;
            completa.chapas.push_back(Chapa{{{copia.id, completa.chapas.size(), 0, 0, gira ? tipo.altura : tipo.largura, gira ? tipo.largura : tipo.altura, gira}}});
        }
    }
    exige(verifica_solucao(instancia, completa).valido, "Geometria do estado inválida.");
    auto calculada = calcula_inviabilidade(estado);
    exige(!menor_inviabilidade(esperado, calculada) && !menor_inviabilidade(calculada, esperado), "Agregação de inviabilidade incorreta.");
}

int main() {
    // Cada campo seguinte pode ser pior: a prioridade anterior continua prevalecendo.
    exige(menor_inviabilidade({0, 99, 9, 99}, {1, 0, 0, 0}), "Excesso não tem prioridade.");
    exige(menor_inviabilidade({1, 0, 99, 99}, {1, 1, 0, 0}), "Área rejeitada não tem prioridade.");
    exige(menor_inviabilidade({1, 1, 1, 99}, {1, 1, 2, 0}), "Quantidade de chapas não tem prioridade.");
    exige(menor_inviabilidade({1, 1, 1, 1}, {1, 1, 1, 2}), "Quantidade de rejeitadas não desempata.");
    exige(!menor_inviabilidade({}, {}), "Empate aceito como melhoria.");
    mt19937 gerador(1001);
    auto instancia = pequena(6, 5, {{5, 4}, {1, 1}, {1, 2}, {5, 3}});
    Solucao origem{{Chapa{{{1, 0, 0, 0, 5, 4, false}}},
                    Chapa{{{2, 1, 0, 0, 1, 1, false}, {3, 1, 1, 0, 1, 2, false}}},
                    Chapa{{{4, 2, 0, 0, 5, 3, false}}}}};
    auto estado_original = cria_estado_reparo(instancia, origem);
    exige(verifica_solucao(instancia, solucao_do_reparo(instancia, estado_original)).valido, "Conversão de ida/volta falhou.");
    auto estado = remove_e_redistribui(instancia, origem, gerador);
    confere(instancia, estado);
    exige(estado.chapas.size() == 2 && estado.chapas[0].pecas == vector<int64_t>({1, 3, 2}), "Remoção, ordem de redistribuição ou menor folga incorretas.");
    exige(estado.chapas[1].pecas == vector<int64_t>{4} && estado.chapas[1].resultado.chapa.posicionamentos[0].indice_chapa == 1, "Reindexação incorreta.");
    exige(estado.chapas[0].empacotamento.tentativas.size() == 8 && estado.chapas[1].empacotamento.tentativas.empty(), "Reempacotou chapa inalterada.");
    exige(origem.chapas.size() == 3 && origem.chapas[1].posicionamentos[0].copia_id == 2, "Alterou a origem.");
    exige(verifica_solucao(instancia, solucao_do_reparo(instancia, estado)).valido, "Não aceitou reparo factível.");
    auto sobrecarga = pequena(10, 1, {{9, 1}, {8, 1}, {3, 1}});
    Solucao tres{{Chapa{{{1, 0, 0, 0, 9, 1, false}}}, Chapa{{{2, 1, 0, 0, 8, 1, false}}}, Chapa{{{3, 2, 0, 0, 3, 1, false}}}}};
    estado = remove_e_redistribui(sobrecarga, tres, gerador);
    confere(sobrecarga, estado);
    exige(estado.chapas[1].pecas == vector<int64_t>({2, 3}) && calcula_inviabilidade(estado).excesso_area == 1, "Não minimizou excesso quando nenhuma chapa tem área suficiente.");
    auto geometria = pequena(5, 4, {{3, 3}, {3, 3}});
    Solucao duas{{Chapa{{{1, 0, 0, 0, 3, 3, false}}}, Chapa{{{2, 1, 0, 0, 3, 3, false}}}}};
    estado = remove_e_redistribui(geometria, duas, gerador);
    confere(geometria, estado);
    exige(estado.chapas[0].pecas == vector<int64_t>({2, 1}), "Empate de ocupação não removeu a primeira chapa.");
    auto medida = calcula_inviabilidade(estado);
    exige(medida.excesso_area == 0 && medida.area_rejeitada == 9 && medida.chapas_inviaveis == 1 && medida.pecas_rejeitadas == 1, "Falha geométrica não medida corretamente.");
    bool falhou = false;
    try { solucao_do_reparo(geometria, estado); }
    catch (const invalid_argument&) { falhou = true; }
    exige(falhou, "Estado inviável virou solução global.");
    auto uma = pequena(2, 2, {{1, 1}});
    auto unica = constroi_solucao_inicial(uma);
    auto antes = gerador;
    falhou = false;
    try { remove_e_redistribui(uma, unica, gerador); }
    catch (const invalid_argument&) { falhou = true; }
    exige(falhou && gerador == antes, "Remoção de última chapa não foi recusada antes dos sorteios.");
    auto corrompido = estado_original;
    swap(corrompido.chapas[0].pecas, corrompido.chapas[2].pecas);
    falhou = false;
    try { solucao_do_reparo(instancia, corrompido); }
    catch (const invalid_argument&) { falhou = true; }
    exige(falhou, "Conversão não conferiu atribuição por chapa.");
    auto invalida = origem;
    invalida.chapas[0].posicionamentos[0].x = -1;
    falhou = false;
    try { remove_e_redistribui(instancia, invalida, gerador); }
    catch (const invalid_argument&) { falhou = true; }
    exige(falhou, "Origem inválida aceita.");
    exige(!melhora_estado(estado_original, estado_original), "Estado empatado aceito.");
    auto grande = le_instancia("tests/data/area_64bits.txt");
    auto grande_inicial = constroi_solucao_inicial(grande);
    auto grande_reparo = remove_e_redistribui(grande, grande_inicial, gerador);
    exige(calcula_inviabilidade(grande_reparo).excesso_area == 10000000000LL, "Excesso truncado em 32 bits.");
    confere(grande, grande_reparo);
    mt19937 dados(1002);
    int testadas = 0;
    for (int teste = 0; teste < 100; teste++) {
        vector<pair<int64_t, int64_t>> dimensoes;
        for (int i = 0; i < 9; i++) dimensoes.push_back({1 + dados() % 4, 1 + dados() % 4});
        auto aleatoria = pequena(6, 5, dimensoes);
        auto inicial = constroi_solucao_inicial(aleatoria);
        if (inicial.chapas.size() < 2) continue;
        mt19937 g1(1001), g2(1001);
        auto a = remove_e_redistribui(aleatoria, inicial, g1);
        auto b = remove_e_redistribui(aleatoria, inicial, g2);
        exige(a.chapas.size() + 1 == inicial.chapas.size() && g1 == g2, "Redução ou estado aleatório incorreto.");
        confere(aleatoria, a);
        exige(!melhora_estado(a, b) && !melhora_estado(b, a), "Inviabilidade não reproduzível.");
        for (size_t c = 0; c < a.chapas.size(); c++) {
            exige(a.chapas[c].pecas == b.chapas[c].pecas && a.chapas[c].resultado.sequencia == b.chapas[c].resultado.sequencia, "Composição/sequência não reproduzível.");
            auto pa = a.chapas[c].resultado.chapa.posicionamentos;
            auto pb = b.chapas[c].resultado.chapa.posicionamentos;
            exige(pa.size() == pb.size() && a.chapas[c].resultado.rejeitadas == b.chapas[c].resultado.rejeitadas, "Colocadas/rejeitadas não reproduzíveis.");
            for (size_t j = 0; j < pa.size(); j++) {
                exige(tie(pa[j].copia_id, pa[j].x, pa[j].y, pa[j].rotacionada) == tie(pb[j].copia_id, pb[j].x, pb[j].y, pb[j].rotacionada), "Geometria não reproduzível.");
            }
        }
        testadas++;
    }
    exige(testadas > 0, "Nenhum caso aleatório foi exercitado.");
    cout << "Estado de reparo: comparação, remoção, conservação, validação e " << testadas << " casos reproduzíveis: OK\n";
}
