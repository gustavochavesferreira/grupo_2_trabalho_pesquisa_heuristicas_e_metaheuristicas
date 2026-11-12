#include "instancia.h"

#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

void verifica(bool condicao, const std::string& mensagem) {
    if (!condicao) {
        throw std::runtime_error(mensagem);
    }
}

int main() {
    auto instancia = le_instancia("tests/data/valida.txt");
    verifica(instancia.caminho == "tests/data/valida.txt", "Caminho de origem incorreto.");
    verifica(instancia.largura == 10 && instancia.altura == 6, "Dimensões da chapa incorretas.");
    verifica(instancia.area_chapa == 60 && instancia.area_total == 75, "Áreas incorretas.");
    verifica(instancia.tipos.size() == 3 && instancia.copias.size() == 6, "Expansão de demandas incorreta.");
    auto tipo = instancia.tipos[0];
    verifica(tipo.id == 2 && tipo.largura == 2 && tipo.altura == 3 && tipo.demanda == 2, "Tipo lido incorretamente.");
    verifica(tipo.limite_copias == 0 && tipo.lucro == 1.5, "Campos auxiliares não preservados.");
    verifica(instancia.tipos[1].limite_copias == -1, "Campo bi foi reinterpretado.");
    verifica(instancia.tipos[1].largura == 6 && instancia.tipos[1].altura == 10, "Orientação original foi alterada.");

    std::set<std::int64_t> ids;
    std::vector<std::int64_t> demandas(3, 0);
    const std::vector<std::size_t> origens = {0, 0, 1, 2, 2, 2};
    for (std::size_t i = 0; i < instancia.copias.size(); ++i) {
        auto copia = instancia.copias[i];
        verifica(copia.id == static_cast<std::int64_t>(i) + 1, "ID de cópia inesperado.");
        verifica(ids.insert(copia.id).second, "ID de cópia duplicado.");
        verifica(copia.indice_tipo == origens[i], "Vínculo com o tipo de origem incorreto.");
        ++demandas.at(copia.indice_tipo);
    }
    for (std::size_t i = 0; i < demandas.size(); ++i) {
        verifica(demandas[i] == instancia.tipos[i].demanda, "Demanda não atendida exatamente.");
    }

    auto repetida = le_instancia("tests/data/valida.txt");
    for (std::size_t i = 0; i < repetida.copias.size(); ++i) {
        verifica(repetida.copias[i].id == instancia.copias[i].id && repetida.copias[i].indice_tipo == instancia.copias[i].indice_tipo,
                 "Leitura repetida alterou a identificação das cópias.");
    }
    auto grande = le_instancia("tests/data/area_64bits.txt");
    verifica(grande.area_chapa == 10000000000LL && grande.area_total == 20000000000LL, "Área truncada em 32 bits.");
    auto espacos = le_instancia("tests/data/espacos_crlf.txt");
    verifica(espacos.copias.size() == 2 && espacos.area_total == 12, "Falha com espaços ou CRLF.");

    const std::vector<std::string> invalidas = {
        "vazia", "sem_tipos", "quantidade_negativa", "quantidade_fracionaria", "chapa_zero", "chapa_negativa",
        "peca_zero", "peca_negativa", "demanda_zero", "demanda_negativa", "id_zero", "id_fora", "id_duplicado",
        "linha_faltante", "linha_extra", "campo_faltante", "campo_extra", "chapa_campo_extra", "nao_numerico",
        "fracao_dimensao", "grande_demais", "overflow_chapa", "overflow_produto", "overflow_soma", "inteiro_fora", "lucro_invalido"
    };
    for (const auto& nome : invalidas) {
        std::string caminho = "tests/data/" + nome + ".txt";
        bool rejeitada = false;
        try {
            le_instancia(caminho);
        } catch (const std::runtime_error& erro) {
            std::string mensagem = erro.what();
            verifica(mensagem.find(caminho) != std::string::npos && mensagem.find("linha") != std::string::npos,
                     "Diagnóstico sem arquivo e linha: " + caminho);
            rejeitada = true;
        }
        verifica(rejeitada, "Instância inválida aceita: " + caminho);
    }

    bool ausente_rejeitada = false;
    try {
        le_instancia("tests/data/arquivo_inexistente.txt");
    } catch (const std::runtime_error& erro) {
        ausente_rejeitada = std::string(erro.what()).find("não foi possível abrir") != std::string::npos;
    }
    verifica(ausente_rejeitada, "Arquivo ausente não diagnosticado.");
    std::cout << "Testes de instância: 3 válidas, " << invalidas.size() << " inválidas e arquivo ausente: OK\n";
    return 0;
}
