#include "solucao.h"

#include <fstream>
#include <stdexcept>
#include <unordered_map>

using namespace std;

void salva_solucao_csv(const Instancia& instancia, const Solucao& solucao, string caminho) {
    auto verificacao = verifica_solucao(instancia, solucao);
    if (!verificacao.valido) {
        throw runtime_error("Solução inválida: " + verificacao.erro);
    }
    unordered_map<int64_t, int64_t> tipos;
    for (CopiaPeca copia : instancia.copias) {
        tipos.emplace(copia.id, instancia.tipos[copia.indice_tipo].id);
    }
    ofstream arquivo(caminho);
    if (!arquivo.is_open()) {
        throw runtime_error("Não foi possível abrir a saída: " + caminho);
    }
    arquivo << "versao,copia_id,tipo_id,chapa,x,y,largura,altura,rotacionada\n";
    for (const Chapa& chapa : solucao.chapas) {
        for (Posicionamento p : chapa.posicionamentos) {
            arquivo << "1," << p.copia_id << ',' << tipos.at(p.copia_id) << ','
                    << p.indice_chapa << ',' << p.x << ',' << p.y << ',' << p.largura << ','
                    << p.altura << ',' << (p.rotacionada ? 1 : 0) << '\n';
        }
    }
    arquivo.close();
    if (!arquivo) {
        throw runtime_error("Falha ao gravar a solução: " + caminho);
    }
}
