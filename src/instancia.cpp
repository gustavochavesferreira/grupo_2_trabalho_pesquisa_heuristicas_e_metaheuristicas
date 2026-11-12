#include "instancia.h"

#include <cmath>
#include <fstream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>

using namespace std;

Instancia le_instancia(string caminho) {
    ifstream arquivo(caminho);
    if (!arquivo.is_open()) {
        throw runtime_error(caminho + ": não foi possível abrir a instância.");
    }

    Instancia instancia;
    instancia.caminho = caminho;
    size_t numero_linha = 0;
    auto falha = [&](string motivo) {
        return runtime_error(caminho + ": linha " + to_string(numero_linha) + ": " + motivo);
    };
    auto proxima_linha = [&]() {
        string linha;
        while (getline(arquivo, linha)) {
            ++numero_linha;
            if (linha.find_first_not_of(" \t\r\n") != string::npos) {
                return istringstream(linha);
            }
        }
        if (arquivo.bad()) {
            throw falha("erro de leitura.");
        }
        throw falha("fim prematuro do arquivo.");
    };
    auto confere_fim_linha = [&](istringstream& linha) {
        linha >> ws;
        if (!linha.eof()) {
            throw falha("campos excedentes ou conteúdo inválido.");
        }
    };

    int64_t quantidade_tipos;
    auto linha = proxima_linha();
    if (!(linha >> quantidade_tipos) || quantidade_tipos <= 0) {
        throw falha("quantidade de tipos deve ser um inteiro positivo.");
    }
    confere_fim_linha(linha);

    linha = proxima_linha();
    if (!(linha >> instancia.largura >> instancia.altura) || instancia.largura <= 0 || instancia.altura <= 0) {
        throw falha("dimensões da chapa devem ser inteiros positivos.");
    }
    confere_fim_linha(linha);
    auto maximo = numeric_limits<int64_t>::max();
    if (instancia.largura > maximo / instancia.altura) {
        throw falha("área da chapa excede a capacidade de 64 bits.");
    }
    instancia.area_chapa = instancia.largura * instancia.altura;

    set<int64_t> ids;
    int64_t total_copias = 0;
    for (int64_t i = 0; i < quantidade_tipos; ++i) {
        linha = proxima_linha();
        TipoPeca tipo;
        if (!(linha >> tipo.id >> tipo.largura >> tipo.altura >> tipo.demanda >> tipo.limite_copias >> tipo.lucro)) {
            throw falha("esperados os campos id wi hi di bi pi, com valores numéricos válidos.");
        }
        confere_fim_linha(linha);
        if (tipo.id < 1 || tipo.id > quantidade_tipos || !ids.insert(tipo.id).second) {
            throw falha("ID deve ser único e pertencer ao intervalo de 1 até a quantidade de tipos.");
        }
        if (tipo.largura <= 0 || tipo.altura <= 0 || tipo.demanda <= 0) {
            throw falha("dimensões e demanda da peça devem ser inteiros positivos.");
        }
        if (!isfinite(tipo.lucro)) {
            throw falha("lucro deve ser finito.");
        }
        bool cabe_direta = tipo.largura <= instancia.largura && tipo.altura <= instancia.altura;
        bool cabe_rotacionada = tipo.altura <= instancia.largura && tipo.largura <= instancia.altura;
        if (!cabe_direta && !cabe_rotacionada) {
            throw falha("peça não cabe em uma chapa, mesmo com rotação.");
        }

        // A peça cabe na chapa: sua área também cabe no inteiro usado para a chapa.
        auto area = tipo.largura * tipo.altura;
        if (tipo.demanda > (maximo - instancia.area_total) / area) {
            throw falha("área total demandada excede a capacidade de 64 bits.");
        }
        instancia.area_total += area * tipo.demanda;
        total_copias += tipo.demanda;
        instancia.tipos.push_back(tipo);
    }

    string restante;
    while (getline(arquivo, restante)) {
        ++numero_linha;
        if (restante.find_first_not_of(" \t\r\n") != string::npos) {
            throw falha("há linhas adicionais após os tipos declarados.");
        }
    }
    if (arquivo.bad()) {
        throw falha("erro de leitura.");
    }

    // A soma das cópias não excede a área total, pois cada peça tem área positiva inteira.
    if (static_cast<uint64_t>(total_copias) > instancia.copias.max_size()) {
        throw falha("quantidade de cópias excede a capacidade do vetor.");
    }
    instancia.copias.reserve(static_cast<size_t>(total_copias));
    for (size_t indice = 0; indice < instancia.tipos.size(); ++indice) {
        for (int64_t j = 0; j < instancia.tipos[indice].demanda; ++j) {
            auto id = static_cast<int64_t>(instancia.copias.size()) + 1;
            instancia.copias.push_back({id, indice});
        }
    }
    return instancia;
}
