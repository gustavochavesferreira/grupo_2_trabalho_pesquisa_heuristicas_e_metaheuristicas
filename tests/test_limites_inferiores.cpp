#include "limites_inferiores.h"

#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>

using namespace std;

void exige(bool ok, string erro) {
    if (!ok) throw runtime_error(erro);
}

Instancia cria(int64_t w, int64_t h, vector<TipoPeca> tipos) {
    Instancia instancia;
    instancia.largura = w;
    instancia.altura = h;
    instancia.area_chapa = w * h;
    instancia.tipos = tipos;
    for (size_t i = 0; i < tipos.size(); i++) {
        auto tipo = tipos[i];
        instancia.area_total += tipo.largura * tipo.altura * tipo.demanda;
        for (int64_t j = 0; j < tipo.demanda; j++) instancia.copias.push_back({static_cast<int64_t>(instancia.copias.size()) + 1, i});
    }
    return instancia;
}

// Referência literal das equações (2)-(8), com quadrados expandidos e todos os q.
// Limitada aos casos pequenos: não compartilha agrupamento, matching ou aritmética da produção.
int64_t referencia_literal(const Instancia& instancia) {
    int64_t w = max(instancia.largura, instancia.altura), h = min(instancia.largura, instancia.altura);
    vector<int64_t> lados;
    for (auto copia : instancia.copias) {
        auto tipo = instancia.tipos[copia.indice_tipo];
        int64_t a = max(tipo.largura, tipo.altura), b = min(tipo.largura, tipo.altura);
        while (b > 1) {
            for (int64_t i = 0; i < a / b; i++) lados.push_back(b);
            int64_t resto = a % b; a = b; b = resto;
        }
    }
    int64_t melhor = 0;
    for (int64_t q = 0; q <= h / 2; q++) {
        vector<int64_t> s2, s3;
        int64_t n1 = 0, area = 0, perda = 0;
        for (int64_t l : lados) {
            if (l > w - q) { n1++; continue; }
            if (2 * l > w) s2.push_back(l);
            else if (2 * l > h) s3.push_back(l);
            else if (l < q) continue;
            area += l * l;
            if ((2 * l > w || 2 * l > h) && l > h - q) perda += l * (h - l);
        }
        sort(s2.begin(), s2.end());
        sort(s3.begin(), s3.end());
        for (int64_t l : s2) {
            auto it = upper_bound(s3.begin(), s3.end(), w - l);
            if (it != s3.begin()) s3.erase(--it);
        }
        int64_t soma = 0;
        for (int64_t l : s3) soma += l;
        int64_t capacidade = w / (h / 2 + 1);
        int64_t ltil = s2.size() + max((soma + w - 1) / w, (static_cast<int64_t>(s3.size()) + capacidade - 1) / capacidade);
        int64_t saldo = area - (w * h * ltil - perda);
        int64_t extra = saldo > 0 ? (saldo + w * h - 1) / (w * h) : 0;
        melhor = max(melhor, n1 + ltil + extra);
    }
    return melhor;
}

// Solução exata por máscaras de células em chapas pequenas, incluindo as duas orientações.
int otimo_exato(const Instancia& instancia) {
    vector<vector<uint32_t>> posicoes;
    for (auto copia : instancia.copias) {
        auto tipo = instancia.tipos[copia.indice_tipo];
        vector<uint32_t> mascaras;
        for (bool gira : {false, true}) {
            int64_t w = gira ? tipo.altura : tipo.largura, h = gira ? tipo.largura : tipo.altura;
            for (int64_t y = 0; y + h <= instancia.altura; y++) {
                for (int64_t x = 0; x + w <= instancia.largura; x++) {
                    uint32_t mascara = 0;
                    for (int64_t dy = 0; dy < h; dy++) {
                        for (int64_t dx = 0; dx < w; dx++) mascara |= uint32_t{1} << ((y + dy) * instancia.largura + x + dx);
                    }
                    mascaras.push_back(mascara);
                }
            }
        }
        posicoes.push_back(mascaras);
    }
    for (size_t k = 1; k <= posicoes.size(); k++) {
        vector<uint32_t> chapas(k, 0);
        function<bool(size_t)> busca = [&](size_t i) {
            if (i == posicoes.size()) return true;
            for (size_t c = 0; c < k; c++) {
                auto anterior = chapas[c];
                for (uint32_t mascara : posicoes[i]) {
                    if ((anterior & mascara) == 0) {
                        chapas[c] = anterior | mascara;
                        if (busca(i + 1)) return true;
                        chapas[c] = anterior;
                    }
                }
                if (anterior == 0) break;
            }
            return false;
        };
        if (busca(0)) return static_cast<int>(k);
    }
    throw runtime_error("Caso de teste inviável.");
}

int main() {
    auto exemplo = cria(23, 20, {{1, 18, 18, 2, 0, 0}, {2, 12, 12, 2, 0, 0}, {3, 11, 11, 5, 0, 0}, {4, 7, 7, 6, 0, 0}});
    auto limites = calcula_limites(exemplo);
    exige(exemplo.area_total == 1835 && limites.por_area == 4 && limites.dell_amico == 6 && limites.referencia == 6, "Exemplo publicado (p. 17) diverge.");
    auto corte = decompoe_quadrados(cria(70, 60, {{1, 70, 60, 1, 0, 0}}));
    exige(corte.size() == 2 && corte[0].lado == 60 && corte[0].quantidade == 1 && corte[1].lado == 10 && corte[1].quantidade == 6, "CUTSQ da Figura 1 diverge.");
    auto residuo = decompoe_quadrados(cria(5, 3, {{1, 3, 5, 2, 0, 0}}));
    exige(residuo.size() == 2 && residuo[0].lado == 3 && residuo[0].quantidade == 2 && residuo[1].lado == 2 && residuo[1].quantidade == 2, "CUTSQ não tratou giro, demanda ou descarte de unidades.");
    limites = calcula_limites(cria(10, 10, {{1, 6, 6, 3, 0, 0}}));
    exige(limites.por_area == 2 && limites.dell_amico == 3, "DMV deveria superar área para três quadrados 6x6.");
    limites = calcula_limites(cria(10, 10, {{1, 5, 5, 4, 0, 0}}));
    exige(limites.referencia == 1, "Fronteira exata W/2 foi classificada como estrita.");
    limites = calcula_limites(cria(10, 1, {{1, 10, 1, 3, 0, 0}}));
    exige(limites.dell_amico == 0 && limites.por_area == 3 && limites.referencia == 3, "Unidades descartadas devem ser recuperadas pelo limite de área.");
    auto grande = cria(3000000000LL, 3000000000LL, {{1, 2000000000LL, 2000000000LL, 2, 0, 0}});
    exige(calcula_limites(grande).referencia == 2, "Produto WH * Ltil não pode causar estouro.");
    grande = cria(3000000000LL, 2500000000LL, {{1, 1600000000LL, 1600000000LL, 3, 0, 0}, {2, 1000000000LL, 1000000000LL, 1, 0, 0}});
    exige(calcula_limites(grande).referencia == 3, "Numerador acima de int64 não foi tratado.");
    auto muitos_quadrados = cria(4000000000000000000LL, 2, {{1, 4000000000000000000LL, 2, 1, 0, 0}});
    exige(calcula_limites(muitos_quadrados).referencia == 1, "CUTSQ agrupado falhou com quantidade enorme de quadrados.");
    auto quase_limite = cria(numeric_limits<int64_t>::max(), 1, {{1, numeric_limits<int64_t>::max(), 1, 1, 0, 0}});
    exige(limite_por_area(quase_limite) == 1, "Arredondamento por área sofreu estouro.");
    exige(abs(desvio_percentual(4, 3) - 100.0 / 3) < 1e-10 && desvio_percentual(3, 3) == 0, "Desvio incorreto.");
    for (auto valores : {pair<int64_t, int64_t>{3, 0}, {3, -1}, {2, 3}}) {
        bool falhou = false;
        try { desvio_percentual(valores.first, valores.second); }
        catch (const invalid_argument&) { falhou = true; }
        exige(falhou, "Desvio aceitou K ou LBref inválido.");
    }
    mt19937 gerador(1001);
    auto sorteia = [&](int64_t limite) { return uniform_int_distribution<int64_t>(1, limite)(gerador); };
    for (int teste = 0; teste < 300; teste++) {
        int64_t w = 1 + sorteia(22), h = 1 + sorteia(20);
        vector<TipoPeca> tipos;
        for (int64_t i = 1; i <= 5; i++) tipos.push_back({i, sorteia(w), sorteia(h), sorteia(3), 0, 0});
        auto instancia = cria(w, h, tipos);
        exige(limite_dell_amico(instancia) == referencia_literal(instancia), "DMV diverge da referência literal com todos os limiares.");
        auto transposta = instancia;
        swap(transposta.largura, transposta.altura);
        for (auto& tipo : transposta.tipos) swap(tipo.largura, tipo.altura);
        exige(calcula_limites(instancia).referencia == calcula_limites(transposta).referencia, "Limite depende da orientação inicial.");
    }
    for (int teste = 0; teste < 60; teste++) {
        vector<TipoPeca> tipos;
        for (int64_t i = 1; i <= 5; i++) tipos.push_back({i, sorteia(4), sorteia(3), 1, 0, 0});
        auto instancia = cria(4, 3, tipos);
        auto lb = calcula_limites(instancia);
        exige(lb.referencia <= otimo_exato(instancia), "Limite excedeu o ótimo exato.");
    }
    cout << "Limites: exemplos publicados/manuais, 300 regressões literais, 60 ótimos exatos e aritmética extrema: OK\n";
}
