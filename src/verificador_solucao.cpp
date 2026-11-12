#include "solucao.h"

#include <unordered_map>

using namespace std;

ResultadoVerificacao verifica_solucao(const Instancia& instancia, const Solucao& solucao) {
    unordered_map<int64_t, size_t> copias;
    for (size_t i = 0; i < instancia.copias.size(); ++i) {
        CopiaPeca copia = instancia.copias[i];
        if (copia.indice_tipo >= instancia.tipos.size() || !copias.emplace(copia.id, i).second) {
            return {false, "Instância com vínculo de tipo inválido ou ID de cópia duplicado."};
        }
    }
    vector<bool> vistas(instancia.copias.size(), false);
    vector<int64_t> demandas(instancia.tipos.size(), 0);
    for (size_t c = 0; c < solucao.chapas.size(); ++c) {
        const vector<Posicionamento>& pecas = solucao.chapas[c].posicionamentos;
        if (pecas.empty()) {
            return {false, "Chapa vazia na solução."};
        }
        for (Posicionamento p : pecas) {
            auto encontrada = copias.find(p.copia_id);
            if (encontrada == copias.end()) {
                return {false, "ID de cópia desconhecido: " + to_string(p.copia_id)};
            }
            auto indice = encontrada->second;
            if (vistas[indice]) {
                return {false, "Cópia duplicada: " + to_string(p.copia_id)};
            }
            vistas[indice] = true;
            auto indice_tipo = instancia.copias[indice].indice_tipo;
            TipoPeca tipo = instancia.tipos[indice_tipo];
            ++demandas[indice_tipo];
            if (p.indice_chapa != c) {
                return {false, "Índice de chapa inconsistente na cópia " + to_string(p.copia_id)};
            }
            auto largura = p.rotacionada ? tipo.altura : tipo.largura;
            auto altura = p.rotacionada ? tipo.largura : tipo.altura;
            if (p.largura != largura || p.altura != altura) {
                return {false, "Dimensões incompatíveis com a orientação da cópia " + to_string(p.copia_id)};
            }
            // Subtrações evitam estouro ao conferir coordenadas fornecidas incorretamente.
            if (p.largura <= 0 || p.altura <= 0 || p.x < 0 || p.y < 0 ||
                p.largura > instancia.largura || p.altura > instancia.altura ||
                p.x > instancia.largura - p.largura || p.y > instancia.altura - p.altura) {
                return {false, "Cópia fora da chapa: " + to_string(p.copia_id)};
            }
        }
        // As somas são seguras após a contenção de todas as peças nesta chapa.
        for (size_t i = 0; i < pecas.size(); ++i) {
            for (size_t j = i + 1; j < pecas.size(); ++j) {
                Posicionamento a = pecas[i];
                Posicionamento b = pecas[j];
                if (a.x < b.x + b.largura && b.x < a.x + a.largura &&
                    a.y < b.y + b.altura && b.y < a.y + a.altura) {
                    return {false, "Sobreposição entre cópias " + to_string(a.copia_id) + " e " + to_string(b.copia_id)};
                }
            }
        }
    }
    for (bool vista : vistas) {
        if (!vista) {
            return {false, "Solução com cópia ausente."};
        }
    }
    for (size_t i = 0; i < demandas.size(); ++i) {
        if (demandas[i] != instancia.tipos[i].demanda) {
            return {false, "Demanda não atendida para o tipo " + to_string(instancia.tipos[i].id)};
        }
    }
    return {true, ""};
}
