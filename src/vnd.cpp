#include "vnd.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <tuple>

using namespace std;

int64_t area_da_copia(const Instancia& instancia, int64_t id) {
    if (id <= 0 || static_cast<uint64_t>(id) > instancia.copias.size()) throw invalid_argument("ID de cópia inválido no VND.");
    auto copia = instancia.copias.at(static_cast<size_t>(id - 1));
    if (copia.id != id) throw invalid_argument("IDs de cópia devem seguir a expansão da instância.");
    auto tipo = instancia.tipos.at(copia.indice_tipo);
    return tipo.largura * tipo.altura;
}

size_t escolhe_origem(const EstadoReparo& estado) {
    size_t origem = estado.chapas.size();
    int64_t maior_excesso = 0;
    for (size_t c = 0; c < estado.chapas.size(); c++) {
        if (estado.chapas[c].empacotamento.excesso_area > maior_excesso) {
            maior_excesso = estado.chapas[c].empacotamento.excesso_area;
            origem = c;
        }
    }
    if (maior_excesso > 0) return origem;
    int64_t maior_rejeicao = 0;
    for (size_t c = 0; c < estado.chapas.size(); c++) {
        if (estado.chapas[c].resultado.area_rejeitada > maior_rejeicao) {
            maior_rejeicao = estado.chapas[c].resultado.area_rejeitada;
            origem = c;
        }
    }
    return origem;
}

vector<int64_t> amostra_bases_uniforme(const EstadoReparo& estado, size_t origem, size_t total_copias, mt19937& gerador) {
    auto pecas = estado.chapas.at(origem).pecas;
    size_t limite = static_cast<size_t>(ceil(sqrt(static_cast<long double>(total_copias))));
    size_t quantidade = min(limite, pecas.size());
    // Fisher-Yates parcial: cada peça restante tem a mesma chance em cada sorteio.
    for (size_t i = 0; i < quantidade; i++) {
        uniform_int_distribution<size_t> sorteio(i, pecas.size() - 1);
        swap(pecas[i], pecas[sorteio(gerador)]);
    }
    pecas.resize(quantidade);
    return pecas;
}

MovimentoExterno cria_movimento(const Instancia& instancia, const EstadoReparo& estado, size_t origem, int64_t base, int vizinhanca, mt19937& gerador) {
    if (vizinhanca < 1 || vizinhanca > 3) throw invalid_argument("Vizinhança deve ser 1, 2 ou 3.");
    const auto& pecas = estado.chapas.at(origem).pecas;
    if (find(pecas.begin(), pecas.end(), base) == pecas.end()) throw invalid_argument("Peça-base não pertence à origem.");
    MovimentoExterno movimento{vizinhanca, origem, estado.chapas.size(), base, -1};
    int64_t area = area_da_copia(instancia, base);
    if (vizinhanca == 3) {
        vector<int64_t> outras;
        for (int64_t id : pecas) if (id != base) outras.push_back(id);
        if (outras.empty()) return movimento;
        uniform_int_distribution<size_t> sorteio(0, outras.size() - 1);
        movimento.parceiro = outras[sorteio(gerador)];
        area += area_da_copia(instancia, movimento.parceiro);
    }
    auto criterio = [&](size_t c) {
        int64_t nova_area = estado.chapas[c].empacotamento.area_total + area;
        return make_tuple(max(int64_t{0}, nova_area - instancia.area_chapa), max(int64_t{0}, instancia.area_chapa - nova_area), c);
    };
    for (size_t c = 0; c < estado.chapas.size(); c++) {
        if (c == origem || (vizinhanca == 2 && estado.chapas[c].pecas.empty())) continue;
        if (movimento.receptora == estado.chapas.size() || criterio(c) < criterio(movimento.receptora)) movimento.receptora = c;
    }
    if (vizinhanca == 2 && movimento.receptora < estado.chapas.size()) {
        auto qualidade_parceiro = [&](int64_t id) {
            int64_t outra_area = area_da_copia(instancia, id);
            int64_t apos_origem = estado.chapas[origem].empacotamento.area_total - area + outra_area;
            int64_t apos_destino = estado.chapas[movimento.receptora].empacotamento.area_total - outra_area + area;
            int64_t sobrecarga = max(int64_t{0}, apos_origem - instancia.area_chapa) + max(int64_t{0}, apos_destino - instancia.area_chapa);
            return make_tuple(sobrecarga, max(area, outra_area) - min(area, outra_area), id);
        };
        for (int64_t id : estado.chapas[movimento.receptora].pecas) {
            if (movimento.parceiro == -1 || qualidade_parceiro(id) < qualidade_parceiro(movimento.parceiro)) movimento.parceiro = id;
        }
    }
    return movimento;
}

void retira_peca(vector<int64_t>& pecas, int64_t id) {
    auto posicao = find(pecas.begin(), pecas.end(), id);
    if (posicao == pecas.end()) throw invalid_argument("Movimento usa peça que não pertence à chapa.");
    pecas.erase(posicao);
}

EstadoReparo aplica_movimento(const Instancia& instancia, const EstadoReparo& estado, MovimentoExterno movimento, mt19937& gerador) {
    if (movimento.vizinhanca < 1 || movimento.vizinhanca > 3 || movimento.origem == movimento.receptora ||
        movimento.origem >= estado.chapas.size() || movimento.receptora >= estado.chapas.size()) throw invalid_argument("Movimento externo inválido.");
    if (movimento.vizinhanca == 3 && movimento.base == movimento.parceiro) throw invalid_argument("O par precisa de duas cópias distintas.");
    auto candidato = estado;
    auto& origem = candidato.chapas[movimento.origem].pecas;
    auto& destino = candidato.chapas[movimento.receptora].pecas;
    retira_peca(origem, movimento.base);
    if (movimento.vizinhanca == 2) {
        retira_peca(destino, movimento.parceiro);
        origem.push_back(movimento.parceiro);
    } else if (movimento.vizinhanca == 3) {
        retira_peca(origem, movimento.parceiro);
        destino.push_back(movimento.parceiro);
    }
    destino.push_back(movimento.base);
    // A ordem crescente mantém o consumo do gerador independente de qual chapa é origem.
    reempacota_chapa(instancia, candidato, min(movimento.origem, movimento.receptora), gerador);
    reempacota_chapa(instancia, candidato, max(movimento.origem, movimento.receptora), gerador);
    return candidato;
}

ResultadoVizinhanca explora_vizinhanca(const Instancia& instancia, const EstadoReparo& estado, int vizinhanca, mt19937& gerador) {
    if (vizinhanca < 1 || vizinhanca > 3) throw invalid_argument("Vizinhança deve ser 1, 2 ou 3.");
    ResultadoVizinhanca resultado;
    resultado.estado = estado;
    size_t origem = escolhe_origem(estado);
    if (origem == estado.chapas.size() || estado.chapas.size() < 2) return resultado;
    resultado.bases = amostra_bases_uniforme(estado, origem, instancia.copias.size(), gerador);
    for (int64_t base : resultado.bases) {
        auto movimento = cria_movimento(instancia, estado, origem, base, vizinhanca, gerador);
        if (movimento.receptora == estado.chapas.size()) continue;
        auto candidato = aplica_movimento(instancia, estado, movimento, gerador);
        resultado.avaliados++;
        if (melhora_estado(candidato, resultado.estado)) {
            resultado.estado = candidato;
            resultado.escolhido = movimento;
            resultado.melhorou = true;
        }
    }
    return resultado;
}

ResultadoVnd executa_vnd(const Instancia& instancia, const EstadoReparo& estado, mt19937& gerador) {
    vector<bool> vistas(instancia.copias.size(), false);
    size_t quantidade = 0;
    for (const ChapaReparo& chapa : estado.chapas) {
        int64_t area = 0;
        for (int64_t id : chapa.pecas) {
            int64_t area_peca = area_da_copia(instancia, id);
            if (vistas[id - 1]) throw invalid_argument("Cópia duplicada na entrada do VND.");
            vistas[id - 1] = true;
            area += area_peca;
            quantidade++;
        }
        if (area != chapa.empacotamento.area_total || max(int64_t{0}, area - instancia.area_chapa) != chapa.empacotamento.excesso_area) throw invalid_argument("Áreas desatualizadas na entrada do VND.");
    }
    if (quantidade != instancia.copias.size()) throw invalid_argument("Cópia ausente na entrada do VND.");
    ResultadoVnd resultado;
    resultado.estado = estado;
    int vizinhanca = 1;
    while (vizinhanca <= 3 && calcula_inviabilidade(resultado.estado).chapas_inviaveis > 0) {
        auto passo = explora_vizinhanca(instancia, resultado.estado, vizinhanca, gerador);
        resultado.avaliacoes[vizinhanca - 1] += passo.avaliados;
        if (passo.melhorou) {
            resultado.estado = passo.estado;
            resultado.melhorias[vizinhanca - 1]++;
            resultado.reinicios++;
            vizinhanca = 1;
        } else {
            vizinhanca++;
        }
    }
    if (calcula_inviabilidade(resultado.estado).chapas_inviaveis == 0) solucao_do_reparo(instancia, resultado.estado);
    return resultado;
}
