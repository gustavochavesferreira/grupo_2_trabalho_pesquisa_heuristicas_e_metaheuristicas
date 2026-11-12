#include "construcao_inicial.h"
#include "decodificador.h"

#include <algorithm>
#include <stdexcept>
#include <tuple>

using namespace std;

Solucao constroi_solucao_inicial(const Instancia& instancia) {
    vector<CopiaPeca> ordenadas = instancia.copias;
    sort(ordenadas.begin(), ordenadas.end(), [&](CopiaPeca a, CopiaPeca b) {
        TipoPeca ta = instancia.tipos.at(a.indice_tipo);
        TipoPeca tb = instancia.tipos.at(b.indice_tipo);
        return make_tuple(ta.largura * ta.altura, max(ta.largura, ta.altura), min(ta.largura, ta.altura), a.id) >
               make_tuple(tb.largura * tb.altura, max(tb.largura, tb.altura), min(tb.largura, tb.altura), b.id);
    });

    Solucao solucao;
    vector<int64_t> areas_ocupadas;
    for (CopiaPeca copia : ordenadas) {
        TipoPeca tipo = instancia.tipos.at(copia.indice_tipo);
        int64_t area = tipo.largura * tipo.altura;
        vector<size_t> candidatas;
        for (size_t c = 0; c < solucao.chapas.size(); c++) {
            if (area <= instancia.area_chapa - areas_ocupadas[c]) candidatas.push_back(c);
        }
        // Para uma mesma peça, menor folga equivale a maior área já ocupada.
        sort(candidatas.begin(), candidatas.end(), [&](size_t a, size_t b) {
            if (areas_ocupadas[a] != areas_ocupadas[b]) return areas_ocupadas[a] > areas_ocupadas[b];
            return a < b;
        });
        bool inseriu = false;
        for (size_t c : candidatas) {
            if (insere_inferior_esquerdo(instancia, copia, solucao.chapas[c], c)) {
                areas_ocupadas[c] += area;
                inseriu = true;
                break;
            }
        }
        if (!inseriu) {
            Chapa nova;
            if (!insere_inferior_esquerdo(instancia, copia, nova, solucao.chapas.size())) {
                throw runtime_error("Cópia não cabe em uma chapa vazia: " + to_string(copia.id));
            }
            solucao.chapas.push_back(nova);
            areas_ocupadas.push_back(area);
        }
    }
    auto verificacao = verifica_solucao(instancia, solucao);
    if (!verificacao.valido) throw runtime_error("Construção inicial inválida: " + verificacao.erro);
    return solucao;
}
