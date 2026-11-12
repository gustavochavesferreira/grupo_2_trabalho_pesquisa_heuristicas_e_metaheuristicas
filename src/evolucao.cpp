#include "evolucao.h"
#include "limites_inferiores.h"

using namespace std;

vector<MarcoEvolucao> calcula_evolucao(const vector<pair<double, int64_t>>& melhorias, int64_t limite_referencia) {
    vector<MarcoEvolucao> marcos;
    size_t proxima = 0;
    int64_t chapas = 0;
    for (double tempo : {0.1, 1.0, 5.0, 10.0, 30.0, 60.0}) {
        while (proxima < melhorias.size() && melhorias[proxima].first <= tempo) chapas = melhorias[proxima++].second;
        marcos.push_back({tempo, chapas > 0, chapas, chapas > 0 ? desvio_percentual(chapas, limite_referencia) : 0});
    }
    return marcos;
}
