#include "construcao_inicial.h"
#include "decodificador.h"

#include <algorithm>
#include <iostream>
#include <random>
#include <stdexcept>
#include <tuple>

using namespace std;

void exige(bool ok, string mensagem) {
    if (!ok) throw runtime_error(mensagem);
}

Instancia pequena(int64_t w, int64_t h, vector<pair<int64_t, int64_t>> dimensoes) {
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

void mesma_solucao(const Solucao& a, const Solucao& b) {
    exige(a.chapas.size() == b.chapas.size(), "Número de chapas diferente.");
    for (size_t c = 0; c < a.chapas.size(); c++) {
        exige(a.chapas[c].posicionamentos.size() == b.chapas[c].posicionamentos.size(), "Quantidade de posições diferente.");
        for (size_t j = 0; j < a.chapas[c].posicionamentos.size(); j++) {
            auto p = a.chapas[c].posicionamentos[j];
            auto q = b.chapas[c].posicionamentos[j];
            exige(tie(p.copia_id, p.indice_chapa, p.x, p.y, p.largura, p.altura, p.rotacionada) ==
                  tie(q.copia_id, q.indice_chapa, q.x, q.y, q.largura, q.altura, q.rotacionada), "Posicionamento diferente.");
        }
    }
}

// Enumera coordenadas inteiras, sem usar a geometria compartilhada ou os pontos de canto.
Solucao oraculo(const Instancia& instancia) {
    auto ordenadas = instancia.copias;
    sort(ordenadas.begin(), ordenadas.end(), [&](CopiaPeca a, CopiaPeca b) {
        auto ta = instancia.tipos[a.indice_tipo];
        auto tb = instancia.tipos[b.indice_tipo];
        return make_tuple(ta.largura * ta.altura, max(ta.largura, ta.altura), min(ta.largura, ta.altura), a.id) >
               make_tuple(tb.largura * tb.altura, max(tb.largura, tb.altura), min(tb.largura, tb.altura), b.id);
    });
    Solucao solucao;
    for (auto copia : ordenadas) {
        auto tipo = instancia.tipos[copia.indice_tipo];
        bool encontrou = false;
        Posicionamento melhor{};
        int64_t menor_folga = 0;
        // O último índice representa a abertura de uma chapa, somente se nenhuma existente servir.
        for (size_t c = 0; c <= solucao.chapas.size(); c++) {
            if (c == solucao.chapas.size() && encontrou) break;
            int64_t ocupada = 0;
            if (c < solucao.chapas.size()) {
                for (auto p : solucao.chapas[c].posicionamentos) ocupada += p.largura * p.altura;
            }
            int64_t folga = instancia.area_chapa - ocupada - tipo.largura * tipo.altura;
            for (int64_t y = 0; y < instancia.altura; y++) {
                for (int64_t x = 0; x < instancia.largura; x++) {
                    for (bool gira : {false, true}) {
                        Posicionamento p{copia.id, c, x, y, gira ? tipo.altura : tipo.largura, gira ? tipo.largura : tipo.altura, gira};
                        if (x + p.largura > instancia.largura || y + p.altura > instancia.altura) continue;
                        bool livre = true;
                        if (c < solucao.chapas.size()) {
                            for (auto q : solucao.chapas[c].posicionamentos) {
                                if (p.x < q.x + q.largura && q.x < p.x + p.largura && p.y < q.y + q.altura && q.y < p.y + p.altura) livre = false;
                            }
                        }
                        if (livre && (!encontrou || make_tuple(folga, c, y, x, gira) < make_tuple(menor_folga, melhor.indice_chapa, melhor.y, melhor.x, melhor.rotacionada))) {
                            encontrou = true;
                            menor_folga = folga;
                            melhor = p;
                        }
                    }
                }
            }
        }
        exige(encontrou, "Instância de teste inviável.");
        if (melhor.indice_chapa == solucao.chapas.size()) solucao.chapas.push_back({});
        solucao.chapas[melhor.indice_chapa].posicionamentos.push_back(melhor);
    }
    return solucao;
}

int main() {
    auto ordenacao = pequena(20, 20, {{2, 6}, {3, 4}, {2, 2}, {2, 6}});
    auto solucao = constroi_solucao_inicial(ordenacao);
    vector<int64_t> ids;
    for (auto p : solucao.chapas[0].posicionamentos) ids.push_back(p.copia_id);
    exige(ids == vector<int64_t>({4, 1, 2, 3}), "Ordenação por área, lados e ID incorreta.");
    auto empate = pequena(3, 3, {{2, 2}, {2, 2}, {1, 1}});
    solucao = constroi_solucao_inicial(empate);
    exige(solucao.chapas.size() == 2 && solucao.chapas[0].posicionamentos.back().copia_id == 3, "Empate de folga não priorizou a primeira chapa.");
    auto bestfit = pequena(6, 5, {{4, 1}, {2, 1}, {5, 2}, {1, 4}, {5, 3}, {2, 2}, {5, 4}});
    solucao = constroi_solucao_inicial(bestfit);
    exige(solucao.chapas.size() == 3, "Não abriu chapa após bloqueio geométrico.");
    exige(solucao.chapas[1].posicionamentos.back().copia_id == 4, "Não escolheu a menor folga entre chapas viáveis.");
    exige(solucao.chapas[2].posicionamentos[0].copia_id == 6, "Peça 2x2 deveria abrir chapa apesar da área livre nas anteriores.");
    mesma_solucao(solucao, oraculo(bestfit));
    auto rotacao = pequena(4, 3, {{3, 3}, {2, 1}});
    solucao = constroi_solucao_inicial(rotacao);
    exige(solucao.chapas.size() == 1 && solucao.chapas[0].posicionamentos[1].rotacionada, "Não aproveitou rotação para inserir na chapa existente.");
    auto vazia_rotacionada = pequena(3, 2, {{2, 3}});
    solucao = constroi_solucao_inicial(vazia_rotacionada);
    exige(solucao.chapas[0].posicionamentos[0].rotacionada, "Não rotacionou para caber na chapa vazia.");
    for (string arquivo : {"valida.txt", "area_64bits.txt", "espacos_crlf.txt"}) {
        auto instancia = le_instancia("tests/data/" + arquivo);
        auto s = constroi_solucao_inicial(instancia);
        exige(verifica_solucao(instancia, s).valido, "Solução rejeitada pelo verificador independente.");
        mesma_solucao(s, constroi_solucao_inicial(instancia));
    }
    Chapa chapa{{{1, 0, 0, 0, 3, 3, false}}};
    auto antes = chapa;
    auto bloqueio = pequena(3, 3, {{3, 3}, {1, 1}});
    exige(!insere_inferior_esquerdo(bloqueio, bloqueio.copias[1], chapa), "Inserção deveria falhar.");
    mesma_solucao(Solucao{{antes}}, Solucao{{chapa}});
    auto invalida = pequena(2, 2, {{3, 3}});
    bool falhou = false;
    try { constroi_solucao_inicial(invalida); }
    catch (const runtime_error&) { falhou = true; }
    exige(falhou, "Construção aceitou peça maior que chapa.");
    mt19937 gerador(1001);
    for (int teste = 0; teste < 100; teste++) {
        vector<pair<int64_t, int64_t>> dimensoes;
        for (int i = 0; i < 10; i++) dimensoes.push_back({1 + gerador() % 5, 1 + gerador() % 5});
        auto instancia = pequena(6, 5, dimensoes);
        auto s = constroi_solucao_inicial(instancia);
        exige(verifica_solucao(instancia, s).valido, "Construção aleatória inválida.");
        mesma_solucao(s, oraculo(instancia));
    }
    cout << "Construção inicial: factibilidade, ordem, folga, bloqueios, rotação e 100 comparações exaustivas: OK\n";
}
