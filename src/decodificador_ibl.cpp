#include "decodificador_ibl.h"

#include <algorithm>
#include <limits>
#include <map>
#include <stdexcept>

using namespace std;

Posicionamento posiciona_ibl(Posicionamento p, const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio) {
    if (p.largura <= 0 || p.altura <= 0 || p.largura > largura || p.altura > altura) throw invalid_argument("Orientação inválida para IBL.");
    p.x = largura - p.largura;
    p.y = altura;
    while (true) {
        verifica_tempo(relogio);
        int64_t x_anterior = p.x, y_anterior = p.y;
        int64_t y = 0;
        size_t examinados = 0;
        for (auto obstaculo : chapa.posicionamentos) {
            if (examinados++ % 64 == 0) verifica_tempo(relogio);
            int64_t topo = obstaculo.y + obstaculo.altura;
            if (obstaculo.x < p.x + p.largura && p.x < obstaculo.x + obstaculo.largura && topo <= p.y) y = max(y, topo);
        }
        p.y = y;
        int64_t x = 0;
        examinados = 0;
        for (auto obstaculo : chapa.posicionamentos) {
            if (examinados++ % 64 == 0) verifica_tempo(relogio);
            // p.y + p.altura pode exceder int64 quando a peça ainda está acima da chapa.
            bool cruza_vertical = p.y < obstaculo.y + obstaculo.altura && (obstaculo.y <= p.y || obstaculo.y - p.y < p.altura);
            int64_t direita = obstaculo.x + obstaculo.largura;
            if (cruza_vertical && direita <= p.x) x = max(x, direita);
        }
        p.x = x;
        if (p.x == x_anterior && p.y == y_anterior) return p;
    }
}

int64_t area_perfil_superior(const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio) {
    if (largura <= 0 || altura <= 0 || largura > numeric_limits<int64_t>::max() / altura) throw invalid_argument("Dimensões inválidas para o perfil.");
    vector<int64_t> bordas{0, largura};
    for (auto p : chapa.posicionamentos) {
        verifica_tempo(relogio);
        if (p.x < 0 || p.y < 0 || p.largura <= 0 || p.altura <= 0 || p.largura > largura || p.altura > altura || p.x > largura - p.largura || p.y > altura - p.altura) throw invalid_argument("Peça fora da chapa no perfil.");
        bordas.push_back(p.x);
        bordas.push_back(p.x + p.largura);
    }
    sort(bordas.begin(), bordas.end());
    bordas.erase(unique(bordas.begin(), bordas.end()), bordas.end());
    int64_t area = 0;
    for (size_t b = 1; b < bordas.size(); b++) {
        verifica_tempo(relogio);
        int64_t topo = 0;
        size_t examinados = 0;
        for (auto p : chapa.posicionamentos) {
            if (examinados++ % 64 == 0) verifica_tempo(relogio);
            if (p.x <= bordas[b - 1] && bordas[b - 1] < p.x + p.largura) topo = max(topo, p.y + p.altura);
        }
        area += (bordas[b] - bordas[b - 1]) * topo;
    }
    return area;
}

__uint128_t calcula_f7(int64_t area_chapa, size_t chapas, int64_t area_perfil) {
    if (area_chapa <= 0 || chapas == 0 || area_perfil <= 0 || area_perfil > area_chapa) throw invalid_argument("Argumentos inválidos para f7.");
    return static_cast<__uint128_t>(area_chapa) * (chapas - 1) + area_perfil;
}

ResultadoIBL decodifica_ibl(const Instancia& instancia, const vector<int64_t>& permutacao, CronometroCpu* relogio) {
    verifica_tempo(relogio);
    if (permutacao.empty() || permutacao.size() != instancia.copias.size()) throw invalid_argument("Permutação IBL deve conter toda a demanda.");
    map<int64_t, size_t> indices;
    vector<vector<int64_t>> copias(instancia.tipos.size());
    for (size_t t = 0; t < instancia.tipos.size(); t++) indices.emplace(instancia.tipos[t].id, t);
    for (auto copia : instancia.copias) copias.at(copia.indice_tipo).push_back(copia.id);
    vector<size_t> usadas(instancia.tipos.size(), 0);
    ResultadoIBL resultado;
    resultado.solucao.chapas.push_back({});
    for (int64_t valor : permutacao) {
        verifica_tempo(relogio);
        if (valor == 0 || valor == numeric_limits<int64_t>::min()) throw invalid_argument("Tipo assinado inválido na permutação IBL.");
        int64_t id = valor < 0 ? -valor : valor;
        auto encontrado = indices.find(id);
        if (encontrado == indices.end()) throw invalid_argument("Tipo desconhecido na permutação IBL.");
        size_t t = encontrado->second;
        if (usadas[t] >= copias[t].size()) throw invalid_argument("Demanda excedida na permutação IBL.");
        auto tipo = instancia.tipos[t];
        bool gira = valor < 0;
        int64_t w = gira ? tipo.altura : tipo.largura, h = gira ? tipo.largura : tipo.altura;
        if (w > instancia.largura || h > instancia.altura) { swap(w, h); gira = !gira; }
        Posicionamento p{copias[t][usadas[t]++], resultado.solucao.chapas.size() - 1, 0, 0, w, h, gira};
        p = posiciona_ibl(p, resultado.solucao.chapas.back(), instancia.largura, instancia.altura, relogio);
        if (p.y > instancia.altura - p.altura) {
            resultado.solucao.chapas.push_back({});
            p.indice_chapa++;
            p.x = 0;
            p.y = 0;
        }
        resultado.solucao.chapas.back().posicionamentos.push_back(p);
    }
    auto verificacao = verifica_solucao(instancia, resultado.solucao);
    if (!verificacao.valido) throw runtime_error("IBL produziu solução inválida: " + verificacao.erro);
    verifica_tempo(relogio);
    resultado.area_perfil = area_perfil_superior(resultado.solucao.chapas.back(), instancia.largura, instancia.altura, relogio);
    resultado.f7 = calcula_f7(instancia.area_chapa, resultado.solucao.chapas.size(), resultado.area_perfil);
    return resultado;
}
