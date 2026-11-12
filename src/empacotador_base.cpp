#include "empacotador_base.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <tuple>
#include <unordered_map>
#include <unordered_set>

using namespace std;

bool melhora_empacotamento(const ResultadoDecodificacao& candidata, const ResultadoDecodificacao& atual) {
    return make_tuple(candidata.area_rejeitada, candidata.rejeitadas.size()) < make_tuple(atual.area_rejeitada, atual.rejeitadas.size());
}

ResultadoEmpacotaBase empacota_base(const Instancia& instancia, const vector<int64_t>& pecas, mt19937& gerador,
                                  const vector<int64_t>& sequencia_anterior, size_t indice_chapa) {
    unordered_map<int64_t, size_t> tipos;
    for (CopiaPeca copia : instancia.copias) tipos.emplace(copia.id, copia.indice_tipo);
    unordered_set<int64_t> conjunto;
    ResultadoEmpacotaBase resultado;
    for (int64_t id : pecas) {
        if (!tipos.count(id) || !conjunto.insert(id).second) throw invalid_argument("Conjunto com cópia desconhecida ou repetida.");
        TipoPeca tipo = instancia.tipos.at(tipos.at(id));
        resultado.area_total += tipo.largura * tipo.altura;
    }
    if (resultado.area_total > instancia.area_chapa) {
        resultado.excesso_area = resultado.area_total - instancia.area_chapa;
        return resultado;
    }

    vector<int64_t> ordenadas = pecas;
    sort(ordenadas.begin(), ordenadas.end(), [&](int64_t a, int64_t b) {
        TipoPeca ta = instancia.tipos.at(tipos.at(a));
        TipoPeca tb = instancia.tipos.at(tipos.at(b));
        return make_tuple(ta.largura * ta.altura, max(ta.largura, ta.altura), min(ta.largura, ta.altura), a) >
               make_tuple(tb.largura * tb.altura, max(tb.largura, tb.altura), min(tb.largura, tb.altura), b);
    });
    vector<int64_t> anterior_atualizada;
    if (!sequencia_anterior.empty()) {
        unordered_set<int64_t> anteriores;
        for (int64_t id : sequencia_anterior) {
            if (!tipos.count(id) || !anteriores.insert(id).second) throw invalid_argument("Sequência anterior com cópia desconhecida ou repetida.");
            if (conjunto.count(id)) anterior_atualizada.push_back(id);
        }
        for (int64_t id : ordenadas) {
            if (!anteriores.count(id)) anterior_atualizada.push_back(id);
        }
    }

    size_t limite_escolha = static_cast<size_t>(ceil(sqrt(static_cast<long double>(pecas.size()))));
    for (int tentativa = 0; tentativa < 8; tentativa++) {
        vector<int64_t> sequencia;
        if (tentativa == 0) {
            sequencia = ordenadas;
        } else if (tentativa == 7 && !sequencia_anterior.empty()) {
            sequencia = anterior_atualizada;
        } else {
            vector<int64_t> restantes = ordenadas;
            while (!restantes.empty()) {
                size_t quantidade = min(limite_escolha, restantes.size());
                uniform_int_distribution<size_t> sorteio(0, quantidade - 1);
                size_t escolhida = sorteio(gerador);
                sequencia.push_back(restantes[escolhida]);
                restantes.erase(restantes.begin() + escolhida);
            }
        }
        resultado.tentativas.push_back(decodifica_inferior_esquerdo(instancia, sequencia, indice_chapa));
        if (resultado.indice_melhor == -1 || melhora_empacotamento(resultado.tentativas.back(), resultado.tentativas[resultado.indice_melhor])) {
            resultado.indice_melhor = tentativa;
        }
    }
    return resultado;
}
