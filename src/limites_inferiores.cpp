#include "limites_inferiores.h"

#include <algorithm>
#include <map>
#include <stdexcept>

using namespace std;

uint64_t divisao_arredondada_acima(uint64_t numerador, uint64_t denominador) {
    return numerador / denominador + (numerador % denominador != 0);
}

vector<GrupoQuadrados> decompoe_quadrados(const Instancia& instancia) {
    map<int64_t, int64_t, greater<int64_t>> contagens;
    for (TipoPeca tipo : instancia.tipos) {
        int64_t w = max(tipo.largura, tipo.altura);
        int64_t h = min(tipo.largura, tipo.altura);
        // CUTSQ (p. 15): corta os maiores quadrados e gira o retângulo residual.
        while (h > 1) {
            contagens[h] += (w / h) * tipo.demanda;
            int64_t resto = w % h;
            w = h;
            h = resto;
        }
    }
    vector<GrupoQuadrados> quadrados;
    for (auto grupo : contagens) quadrados.push_back({grupo.first, grupo.second});
    return quadrados;
}

int64_t limite_por_area(const Instancia& instancia) {
    if (instancia.area_chapa <= 0 || instancia.area_total < 0) throw invalid_argument("Áreas inválidas para calcular o limite.");
    return static_cast<int64_t>(divisao_arredondada_acima(instancia.area_total, instancia.area_chapa));
}

// Equações (2)-(7), com W >= H e grupos em ordem decrescente de lado.
int64_t avalia_limiar_dmv(int64_t w, int64_t h, const vector<GrupoQuadrados>& quadrados, int64_t q) {
    uint64_t s1 = 0, quantidade_s2 = 0;
    uint64_t area_s234 = 0, desperdicio_s23 = 0;
    vector<GrupoQuadrados> s2, s3;
    for (GrupoQuadrados grupo : quadrados) {
        int64_t lado = grupo.lado;
        uint64_t quantidade = grupo.quantidade;
        if (lado > w - q) {
            s1 += quantidade;
            continue;
        }
        if (lado > w / 2) {
            s2.push_back(grupo);
            quantidade_s2 += quantidade;
        } else if (lado > h / 2) {
            s3.push_back(grupo);
        } else if (lado < q) {
            continue;
        }
        area_s234 += quantidade * lado * lado;
        if (lado > h / 2 && lado > h - q) desperdicio_s23 += quantidade * lado * (h - lado);
    }

    // S2 em ordem crescente dá os espaços residuais em ordem decrescente.
    // Emparelha-se cada espaço com o maior quadrado de S3 que couber (Lema 2).
    size_t proximo = 0;
    for (auto it = s2.rbegin(); it != s2.rend(); ++it) {
        int64_t vagas = it->quantidade;
        while (vagas > 0 && proximo < s3.size()) {
            if (s3[proximo].lado > w - it->lado) {
                proximo++;
                continue;
            }
            int64_t usados = min(vagas, s3[proximo].quantidade);
            vagas -= usados;
            s3[proximo].quantidade -= usados;
            if (s3[proximo].quantidade == 0) proximo++;
        }
    }
    uint64_t quantidade_restante = 0, soma_lados_restantes = 0;
    for (GrupoQuadrados grupo : s3) {
        quantidade_restante += grupo.quantidade;
        soma_lados_restantes += static_cast<uint64_t>(grupo.quantidade) * grupo.lado;
    }
    uint64_t por_largura = divisao_arredondada_acima(soma_lados_restantes, w);
    uint64_t por_quantidade = divisao_arredondada_acima(quantidade_restante, w / (h / 2 + 1));
    uint64_t l_til = quantidade_s2 + max(por_largura, por_quantidade);

    // (7) equivale a |S1| + max(L_til, ceil((área + desperdício) / WH)).
    // Cada desperdício é menor que a área do próprio quadrado. A soma cabe em
    // uint64_t, mesmo quando excede int64_t; evita-se o produto WH * L_til.
    uint64_t por_area = divisao_arredondada_acima(area_s234 + desperdicio_s23, static_cast<uint64_t>(w) * h);
    return static_cast<int64_t>(s1 + max(l_til, por_area));
}

int64_t limite_dell_amico(const Instancia& instancia) {
    int64_t w = max(instancia.largura, instancia.altura);
    int64_t h = min(instancia.largura, instancia.altura);
    if (h <= 0) throw invalid_argument("Dimensões inválidas para calcular o limite.");
    auto quadrados = decompoe_quadrados(instancia);
    // Corolário 4: basta examinar os lados distintos até H/2, além de q=0.
    int64_t limite = avalia_limiar_dmv(w, h, quadrados, 0);
    for (GrupoQuadrados grupo : quadrados) {
        if (grupo.lado <= h / 2) limite = max(limite, avalia_limiar_dmv(w, h, quadrados, grupo.lado));
    }
    return limite;
}

LimitesInferiores calcula_limites(const Instancia& instancia) {
    int64_t area = limite_por_area(instancia);
    int64_t dmv = limite_dell_amico(instancia);
    return {area, dmv, max(area, dmv)};
}

double desvio_percentual(int64_t chapas, int64_t limite_referencia) {
    if (limite_referencia <= 0 || chapas < limite_referencia) throw invalid_argument("LBref deve ser positivo e K deve ser maior ou igual a LBref.");
    return static_cast<double>(100.0L * (chapas - limite_referencia) / limite_referencia);
}
