#include "decodificador.h"

#include <algorithm>
#include <iostream>
#include <random>
#include <set>
#include <stdexcept>
#include <tuple>

using namespace std;

void confere(bool ok, string erro) {
    if (!ok) throw runtime_error(erro);
}

Instancia pequena(int64_t w, int64_t h, vector<pair<int64_t, int64_t>> dimensoes) {
    Instancia instancia;
    instancia.largura = w;
    instancia.altura = h;
    instancia.area_chapa = w * h;
    for (auto dimensao : dimensoes) {
        auto id = static_cast<int64_t>(instancia.tipos.size()) + 1;
        instancia.copias.push_back({id, instancia.tipos.size()});
        instancia.tipos.push_back({id, dimensao.first, dimensao.second, 1, 0, 0});
        instancia.area_total += dimensao.first * dimensao.second;
    }
    return instancia;
}

// Oráculo por todos os pontos inteiros, sem usar a geometria nem os cantos do decodificador.
void compara_com_exaustao(const Instancia& instancia, const vector<int64_t>& sequencia) {
    auto resultado = decodifica_inferior_esquerdo(instancia, sequencia);
    Chapa prefixo;
    vector<int64_t> rejeitadas;
    int64_t area_rejeitada = 0;
    for (int64_t id : sequencia) {
        TipoPeca tipo = instancia.tipos[id - 1];
        bool achou = false;
        Posicionamento melhor{};
        for (int64_t y = 0; y < instancia.altura; y++) {
            for (int64_t x = 0; x < instancia.largura; x++) {
                for (bool gira : {false, true}) {
                    Posicionamento p{id, 0, x, y, gira ? tipo.altura : tipo.largura, gira ? tipo.largura : tipo.altura, gira};
                    if (x + p.largura > instancia.largura || y + p.altura > instancia.altura) continue;
                    bool livre = true;
                    for (Posicionamento q : prefixo.posicionamentos) {
                        if (p.x < q.x + q.largura && q.x < p.x + p.largura && p.y < q.y + q.altura && q.y < p.y + p.altura) livre = false;
                    }
                    if (livre && (!achou || tie(p.y, p.x, p.rotacionada) < tie(melhor.y, melhor.x, melhor.rotacionada))) {
                        achou = true;
                        melhor = p;
                    }
                }
            }
        }
        if (achou) {
            auto indice = prefixo.posicionamentos.size();
            confere(indice < resultado.chapa.posicionamentos.size(), "Oráculo encontrou colocação omitida.");
            auto p = resultado.chapa.posicionamentos[indice];
            confere(tie(p.copia_id, p.x, p.y, p.largura, p.altura, p.rotacionada) ==
                    tie(melhor.copia_id, melhor.x, melhor.y, melhor.largura, melhor.altura, melhor.rotacionada), "Desempate ou posição diverge do oráculo.");
            prefixo.posicionamentos.push_back(melhor);
        } else {
            rejeitadas.push_back(id);
            area_rejeitada += tipo.largura * tipo.altura;
        }
    }
    confere(resultado.sequencia == sequencia && resultado.rejeitadas == rejeitadas && resultado.area_rejeitada == area_rejeitada, "Ordem ou rejeições incorretas.");
    confere(prefixo.posicionamentos.size() == resultado.chapa.posicionamentos.size(), "Peças excedentes.");
    Solucao completa;
    if (!resultado.chapa.posicionamentos.empty()) completa.chapas.push_back(resultado.chapa);
    for (int64_t id : rejeitadas) {
        TipoPeca tipo = instancia.tipos[id - 1];
        bool gira = tipo.largura > instancia.largura || tipo.altura > instancia.altura;
        completa.chapas.push_back(Chapa{{{id, completa.chapas.size(), 0, 0, gira ? tipo.altura : tipo.largura, gira ? tipo.largura : tipo.altura, gira}}});
    }
    confere(verifica_solucao(instancia, completa).valido, "Verificador independente rejeitou conservação/geometria.");
}

int main() {
    auto instancia = pequena(4, 3, {{3, 2}, {3, 2}, {1, 1}, {1, 1}});
    auto r = decodifica_inferior_esquerdo(instancia, {1, 2, 3, 4}, 7);
    confere(r.rejeitadas == vector<int64_t>{2} && r.area_rejeitada == 6, "Rejeição incorreta.");
    confere(r.primeira_rejeitada == 2 && r.posicao_primeira_rejeitada == 1, "Primeira rejeição incorreta.");
    confere(r.chapa.posicionamentos.size() == 3 && r.chapa.posicionamentos[1].copia_id == 3, "Não continuou após rejeição.");
    for (auto p : r.chapa.posicionamentos) confere(p.indice_chapa == 7, "Índice da chapa perdido.");
    compara_com_exaustao(instancia, {1, 2, 3, 4});
    auto rotacao = pequena(3, 2, {{2, 3}});
    r = decodifica_inferior_esquerdo(rotacao, {1});
    confere(r.chapa.posicionamentos[0].rotacionada && r.primeira_rejeitada == -1 && r.posicao_primeira_rejeitada == -1, "Rotação obrigatória ou sentinela incorreta.");
    confere(decodifica_inferior_esquerdo(instancia, {}).chapa.posicionamentos.empty(), "Sequência vazia incorreta.");
    confere(decodifica_inferior_esquerdo(instancia, {3}).sequencia == vector<int64_t>{3}, "Subconjunto rejeitado.");
    auto quadrados = pequena(2, 2, {{2, 2}, {2, 2}, {2, 2}});
    auto bloqueado = decodifica_inferior_esquerdo(quadrados, {1, 2, 3});
    confere(bloqueado.rejeitadas == vector<int64_t>({2, 3}) && bloqueado.area_rejeitada == 8,
            "Bloqueio total ou soma de rejeições incorretos.");
    confere(!bloqueado.chapa.posicionamentos[0].rotacionada, "Desempate de quadrado incorreto.");
    for (vector<int64_t> invalida : {vector<int64_t>{1, 1}, vector<int64_t>{99}}) {
        bool falhou = false;
        try { decodifica_inferior_esquerdo(instancia, invalida); }
        catch (const invalid_argument&) { falhou = true; }
        confere(falhou, "Sequência inválida aceita.");
    }
    Chapa chapa{{{1, 0, 0, 0, 2, 2, false}, {2, 0, 2, 0, 2, 2, false}}};
    auto pontos = pontos_canto(chapa, 4, 4);
    confere(pontos.size() == 2 && pontos[0].x == 0 && pontos[0].y == 2 && pontos[1].x == 2 && pontos[1].y == 2, "Pontos duplicados, ocupados ou nas bordas não removidos.");
    confere(!sobrepoe(chapa.posicionamentos[0], chapa.posicionamentos[1]), "Contato de borda detectado como colisão.");
    auto grande = le_instancia("tests/data/area_64bits.txt");
    r = decodifica_inferior_esquerdo(grande, {1, 2});
    confere(r.area_rejeitada == 10000000000LL, "Área rejeitada truncada.");
    mt19937 gerador(1001);
    for (int teste = 0; teste < 200; teste++) {
        vector<pair<int64_t, int64_t>> dimensoes;
        for (int i = 0; i < 8; i++) dimensoes.push_back({1 + gerador() % 5, 1 + gerador() % 5});
        auto aleatoria = pequena(6, 5, dimensoes);
        vector<int64_t> sequencia{1, 2, 3, 4, 5, 6, 7, 8};
        shuffle(sequencia.begin(), sequencia.end(), gerador);
        compara_com_exaustao(aleatoria, sequencia);
    }
    cout << "Geometria e decodificador: casos dirigidos e 200 comparações com oráculo exaustivo: OK\n";
}
