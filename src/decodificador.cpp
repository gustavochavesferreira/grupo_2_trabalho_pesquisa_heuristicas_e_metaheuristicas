#include "decodificador.h"

#include <stdexcept>
#include <tuple>
#include <unordered_map>
#include <unordered_set>

using namespace std;

ResultadoDecodificacao decodifica_inferior_esquerdo(const Instancia& instancia, const vector<int64_t>& sequencia, size_t indice_chapa) {
    unordered_map<int64_t, size_t> tipos;
    for (CopiaPeca copia : instancia.copias) tipos.emplace(copia.id, copia.indice_tipo);
    unordered_set<int64_t> vistas;
    for (int64_t id : sequencia) {
        if (!tipos.count(id) || !vistas.insert(id).second) throw invalid_argument("Sequência com cópia desconhecida ou repetida.");
    }
    ResultadoDecodificacao resultado;
    resultado.sequencia = sequencia;
    for (size_t i = 0; i < sequencia.size(); ++i) {
        int64_t id = sequencia[i];
        TipoPeca tipo = instancia.tipos.at(tipos.at(id));
        bool encontrou = false;
        Posicionamento melhor{};
        auto pontos = pontos_canto(resultado.chapa, instancia.largura, instancia.altura);
        for (PontoCanto ponto : pontos) {
            for (bool gira : {false, true}) {
                if (gira && tipo.largura == tipo.altura) continue;
                Posicionamento p{id, indice_chapa, ponto.x, ponto.y,
                                 gira ? tipo.altura : tipo.largura, gira ? tipo.largura : tipo.altura, gira};
                if (!posicao_livre(p, resultado.chapa, instancia.largura, instancia.altura)) continue;
                // Pontos que ainda permitem descer ou ir à esquerda são redundantes para esta orientação.
                auto anterior = p;
                anterior.y--;
                if (posicao_livre(anterior, resultado.chapa, instancia.largura, instancia.altura)) continue;
                anterior = p;
                anterior.x--;
                if (posicao_livre(anterior, resultado.chapa, instancia.largura, instancia.altura)) continue;
                if (!encontrou || tie(p.y, p.x, p.rotacionada) < tie(melhor.y, melhor.x, melhor.rotacionada)) {
                    melhor = p;
                    encontrou = true;
                }
            }
        }
        if (encontrou) {
            resultado.chapa.posicionamentos.push_back(melhor);
        } else {
            resultado.rejeitadas.push_back(id);
            resultado.area_rejeitada += tipo.largura * tipo.altura;
            if (resultado.primeira_rejeitada == -1) {
                resultado.primeira_rejeitada = id;
                resultado.posicao_primeira_rejeitada = static_cast<int64_t>(i);
            }
        }
    }
    return resultado;
}
