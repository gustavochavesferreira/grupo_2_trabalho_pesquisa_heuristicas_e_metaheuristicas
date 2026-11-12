#include "geometria.h"

#include <algorithm>
#include <stdexcept>
#include <tuple>

using namespace std;

bool contido_na_chapa(Posicionamento p, int64_t largura, int64_t altura) {
    return p.x >= 0 && p.y >= 0 && p.largura > 0 && p.altura > 0 &&
           p.largura <= largura && p.altura <= altura &&
           p.x <= largura - p.largura && p.y <= altura - p.altura;
}

bool sobrepoe(Posicionamento a, Posicionamento b) {
    // Compara distâncias, evitando somar coordenadas que possam estar no limite inteiro.
    bool horizontal = a.x <= b.x ? static_cast<uint64_t>(b.x) - static_cast<uint64_t>(a.x) < static_cast<uint64_t>(a.largura)
                                : static_cast<uint64_t>(a.x) - static_cast<uint64_t>(b.x) < static_cast<uint64_t>(b.largura);
    bool vertical = a.y <= b.y ? static_cast<uint64_t>(b.y) - static_cast<uint64_t>(a.y) < static_cast<uint64_t>(a.altura)
                              : static_cast<uint64_t>(a.y) - static_cast<uint64_t>(b.y) < static_cast<uint64_t>(b.altura);
    return a.largura > 0 && a.altura > 0 && b.largura > 0 && b.altura > 0 && horizontal && vertical;
}

bool posicao_livre(Posicionamento p, const Chapa& chapa, int64_t largura, int64_t altura) {
    if (!contido_na_chapa(p, largura, altura)) return false;
    for (Posicionamento outra : chapa.posicionamentos) {
        if (sobrepoe(p, outra)) return false;
    }
    return true;
}

void coordenadas_canto(const Chapa& chapa, int64_t largura, int64_t altura, vector<int64_t>& xs, vector<int64_t>& ys) {
    xs = {0};
    ys = {0};
    for (Posicionamento p : chapa.posicionamentos) {
        if (!contido_na_chapa(p, largura, altura)) throw invalid_argument("Chapa contém posicionamento fora dos limites.");
        if (p.x + p.largura < largura) xs.push_back(p.x + p.largura);
        if (p.y + p.altura < altura) ys.push_back(p.y + p.altura);
    }
    sort(xs.begin(), xs.end());
    xs.erase(unique(xs.begin(), xs.end()), xs.end());
    sort(ys.begin(), ys.end());
    ys.erase(unique(ys.begin(), ys.end()), ys.end());
}

vector<PontoCanto> pontos_canto(const Chapa& chapa, int64_t largura, int64_t altura, CronometroCpu* relogio) {
    vector<int64_t> xs, ys;
    coordenadas_canto(chapa, largura, altura, xs, ys);
    vector<PontoCanto> pontos;
    // Projeções cruzadas incluem cantos criados por bordas de peças diferentes.
    for (int64_t y : ys) {
        for (int64_t x : xs) {
            verifica_tempo(relogio);
            bool ocupado = false;
            for (Posicionamento p : chapa.posicionamentos) {
                if (x >= p.x && x < p.x + p.largura && y >= p.y && y < p.y + p.altura) {
                    ocupado = true;
                    break;
                }
            }
            if (!ocupado && x < largura && y < altura) pontos.push_back({x, y});
        }
    }
    return pontos;
}
